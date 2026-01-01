from flask import Flask, request, jsonify, session, abort
from werkzeug.utils import secure_filename
from sqlalchemy import or_

from .config import Config
from .database import db
from .db_models import Book, UserBook, Summary, User
from .auth import (
    register_user,
    login_user,
    logout_user,
    is_logged_in,
    current_user_id,
    is_admin
)
from .file_utils import (
    extract_text_from_txt,
    extract_text_from_pdf,
    extract_text_from_docx,
    validate_extracted_text
)
from .hash_utils import generate_content_hash
from werkzeug.security import generate_password_hash

from backend.text_preprocessing import preprocess_text
from backend.models.summarizer import summarizer

import time
import traceback

from flask import send_file
from backend.utils.export_utils import generate_txt, generate_pdf

# ---------- OPTIONAL POST PROCESSOR (SAFE) ----------
try:
    from backend.utils.summary_postprocess import SummaryPostProcessor
except ImportError:
    SummaryPostProcessor = None

# -------------------- CONSTANTS --------------------
ALLOWED_EXTENSIONS = {"txt", "pdf", "docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# -------------------- HELPERS --------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required():
    if not is_logged_in():
        abort(401)


def admin_required():
    if not is_logged_in() or not is_admin():
        abort(403)


# -------------------- APP FACTORY --------------------
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    post_processor = (
        SummaryPostProcessor(min_words=40, max_words=120)
        if SummaryPostProcessor else None
    )

    # =================================================
    # AUTH
    # =================================================
    @app.route("/me", methods=["GET"])
    def me():
        if "user_id" not in session:
            return {"authenticated": False}, 401
        return {
            "authenticated": True,
            "user_id": session["user_id"],
            "role": session["role"]
        }

    @app.route("/register", methods=["POST"])
    def register():
        data = request.json
        ok, msg = register_user(
            data.get("username"),
            data.get("email"),
            data.get("password")
        )
        return jsonify({"message": msg}), 200 if ok else 400

    @app.route("/login", methods=["POST"])
    def login():
        data = request.json
        ok, msg = login_user(
            data.get("email"),
            data.get("password")
        )
        return jsonify({"message": msg}), 200 if ok else 401

    @app.route("/logout", methods=["POST"])
    def logout():
        login_required()
        logout_user()
        return jsonify({"message": "Logged out"})

    # =================================================
    # BOOK LIST
    # =================================================
    @app.route("/books", methods=["GET"])
    def get_books():
        login_required()

        search = request.args.get("search", "")
        sort_by = request.args.get("sort", "date_desc")

        query = Book.query if is_admin() else (
            Book.query.join(UserBook)
            .filter(UserBook.user_id == current_user_id())
        )

        if search:
            query = query.filter(
                or_(
                    Book.title.ilike(f"%{search}%"),
                    Book.author.ilike(f"%{search}%")
                )
            )

        if sort_by == "title_asc":
            query = query.order_by(Book.title.asc())
        elif sort_by == "title_desc":
            query = query.order_by(Book.title.desc())
        else:
            query = query.order_by(Book.created_at.desc())

        books = []
        for b in query.all():
            books.append({
                "book_id": b.book_id,
                "title": b.title,
                "author": b.author,
                "uploaded": b.created_at.isoformat(),
                "has_summary": Summary.query.filter_by(book_id=b.book_id).count() > 0
            })

        return jsonify({"books": books})

    # =================================================
    # BOOK DETAILS
    # =================================================
    @app.route("/books/<int:book_id>/details", methods=["GET"])
    def book_details(book_id):
        login_required()
        book = Book.query.get_or_404(book_id)

        if not is_admin():
            if not UserBook.query.filter_by(
                user_id=current_user_id(),
                book_id=book.book_id
            ).first():
                abort(403)

        text = book.original_text
        return jsonify({
            "title": book.title,
            "author": book.author,
            "file_type": book.file_type,
            "uploaded_date": book.created_at.strftime("%Y-%m-%d %H:%M"),
            "word_count": len(text.split()),
            "char_count": len(text),
            "line_count": len(text.splitlines())
        })

    # =================================================
    # SUMMARY GENERATION (TASK 13 CORE)
    # =================================================
    @app.route("/books/<int:book_id>/summarize", methods=["POST"])
    def summarize_book(book_id):
        login_required()
        book = Book.query.get_or_404(book_id)

        if not is_admin():
            if not UserBook.query.filter_by(
                user_id=current_user_id(),
                book_id=book.book_id
            ).first():
                abort(403)

        try:
            start = time.time()

            text = book.original_text[:2500]
            raw = summarizer.summarize(text, sentences=4)

            if post_processor:
                refined = post_processor.refine(raw, book.original_text)
                final_text = refined["summary"]
                length = refined["word_count"]
            else:
                final_text = raw
                length = len(raw.split())

            last_version = (
                db.session.query(db.func.max(Summary.version))
                .filter_by(book_id=book.book_id)
                .scalar()
            ) or 0

            summary = Summary(
                book_id=book.book_id,
                user_id=current_user_id(),
                summary_text=final_text,
                summary_length=length,
                model_used="textrank",
                version=last_version + 1
            )

            db.session.add(summary)
            db.session.commit()

            return jsonify({
                "summary_id": summary.summary_id,
                "summary": final_text,
                "version": summary.version,
                "length": length,
                "time_taken": round(time.time() - start, 2)
            })


        except Exception as e:
            traceback.print_exc()
            return jsonify({
                "error": "Summarization failed",
                "details": str(e)
            }), 500

    # =================================================
    # SUMMARY MANAGEMENT
    # =================================================
    @app.route("/books/<int:book_id>/summaries", methods=["GET"])
    def get_book_summaries(book_id):
        login_required()

        if not is_admin():
            if not UserBook.query.filter_by(
                user_id=current_user_id(),
                book_id=book_id
            ).first():
                abort(403)

        summaries = Summary.query.filter_by(book_id=book_id).order_by(
            Summary.created_at.desc()
        ).all()

        return jsonify({
            "summaries": [
                {
                    "summary_id": s.summary_id,
                    "version": s.version,
                    "model": s.model_used,
                    "length": s.summary_length,
                    "created_at": s.created_at.isoformat()
                } for s in summaries
            ]
        })

    @app.route("/summaries/<int:summary_id>", methods=["GET"])
    def get_summary(summary_id):
        login_required()
        s = Summary.query.get_or_404(summary_id)
        return jsonify({
            "summary_text": s.summary_text,
            "version": s.version,
            "model": s.model_used,
            "created_at": s.created_at.isoformat()
        })

    @app.route("/summaries/<int:summary_id>", methods=["DELETE"])
    def delete_summary(summary_id):
        admin_required()
        s = Summary.query.get_or_404(summary_id)
        db.session.delete(s)
        db.session.commit()
        return jsonify({"message": "Summary deleted"})

    # =================================================
    # ADMIN ANALYTICS
    # =================================================
    @app.route("/admin/analytics", methods=["GET"])
    def admin_analytics():
        admin_required()

        total = Summary.query.count()
        avg_len = db.session.query(
            db.func.avg(Summary.summary_length)
        ).scalar() or 0

        active = (
            db.session.query(User.username, db.func.count(Summary.summary_id))
            .join(Summary, Summary.user_id == User.user_id)
            .group_by(User.username)
            .order_by(db.func.count(Summary.summary_id).desc())
            .limit(5)
            .all()
        )

        return jsonify({
            "total_summaries": total,
            "average_length": round(avg_len, 2),
            "most_active_users": [
                {"username": u, "summaries": c} for u, c in active
            ]
        })

    # =================================================
    # FILE UPLOAD
    # =================================================
    @app.route("/upload/file", methods=["POST"])
    def upload_file():
        login_required()

        if "file" not in request.files:
            return jsonify({"error": "No file"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "Empty filename"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400

        ext = file.filename.rsplit(".", 1)[1].lower()

        if ext == "txt":
            text = extract_text_from_txt(file)
        elif ext == "pdf":
            text = extract_text_from_pdf(file)
        else:
            text = extract_text_from_docx(file)

        text = validate_extracted_text(text)
        content_hash = generate_content_hash(text)

        book = Book.query.filter_by(content_hash=content_hash).first()
        if not book:
            book = Book(
                title=secure_filename(file.filename),
                original_text=text,
                file_type=ext,
                content_hash=content_hash
            )
            db.session.add(book)
            db.session.commit()

        if not UserBook.query.filter_by(
            user_id=current_user_id(),
            book_id=book.book_id
        ).first():
            db.session.add(UserBook(
                user_id=current_user_id(),
                book_id=book.book_id
            ))
            db.session.commit()

        return jsonify({"message": "File uploaded"})

    @app.route("/summaries/<int:summary_id>/export", methods=["GET"])
    def export_summary(summary_id):
        login_required()

        format_type = request.args.get("format", "txt")
        include_original = request.args.get("include_original", "false").lower() == "true"

        summary = Summary.query.get_or_404(summary_id)
        book = Book.query.get_or_404(summary.book_id)

        # Authorization
        if not is_admin():
            link = UserBook.query.filter_by(
                user_id=current_user_id(),
                book_id=book.book_id
            ).first()
            if not link:
                abort(403)

        if format_type == "pdf":
            file_data = generate_pdf(
                summary.summary_text,
                title=book.title,
                author=book.author,
                include_original=include_original,
                original_text=book.original_text
            )
            return send_file(
                file_data,
                as_attachment=True,
                download_name=f"{book.title}_summary.pdf",
                mimetype="application/pdf"
            )

        # Default: TXT
        file_data = generate_txt(
            summary.summary_text,
            title=book.title,
            author=book.author,
            include_original=include_original,
            original_text=book.original_text,
            generated_at=summary.created_at,
            version=summary.version,
            model=summary.model_used
        )
        return send_file(
            file_data,
            as_attachment=True,
            download_name=f"{book.title}_summary.txt",
            mimetype="text/plain"
    )

    @app.route("/books/<int:book_id>/summary-history", methods=["GET"])
    def summary_history(book_id):
        login_required()

        summaries = Summary.query.filter_by(book_id=book_id).order_by(
            Summary.version.desc()
        ).all()

        return jsonify({
            "summaries": [
                {
                    "summary_id": s.summary_id,
                    "version": s.version,
                    "model": s.model_used,
                    "created_at": s.created_at.isoformat(),
                    "is_favorite": s.is_favorite,
                    "is_default": s.is_default
                } for s in summaries
            ]
        })
        
    import difflib

    @app.route("/summaries/compare", methods=["GET"])
    def compare_summaries():
        login_required()

        id1 = request.args.get("id1", type=int)
        id2 = request.args.get("id2", type=int)

        s1 = Summary.query.get_or_404(id1)
        s2 = Summary.query.get_or_404(id2)

        diff = difflib.HtmlDiff().make_table(
            s1.summary_text.splitlines(),
            s2.summary_text.splitlines(),
            fromdesc=f"Version {s1.version}",
            todesc=f"Version {s2.version}",
            context=True
        )

        return jsonify({
            "diff_html": diff
        })

    @app.route("/summaries/<int:summary_id>/favorite", methods=["POST"])
    def mark_favorite(summary_id):
        login_required()

        s = Summary.query.get_or_404(summary_id)
        s.is_favorite = True
        db.session.commit()

        return jsonify({"message": "Marked as favorite"})

    @app.route("/summaries/<int:summary_id>/set-default", methods=["POST"])
    def set_default(summary_id):
        login_required()

        s = Summary.query.get_or_404(summary_id)

        Summary.query.filter_by(
            book_id=s.book_id,
            is_default=True
        ).update({"is_default": False})

        s.is_default = True
        db.session.commit()

        return jsonify({"message": "Default summary set"})

    @app.route("/summaries/<int:summary_id>/restore", methods=["POST"])
    def restore_summary(summary_id):
        login_required()

        old = Summary.query.get_or_404(summary_id)

        last_version = (
            db.session.query(db.func.max(Summary.version))
            .filter_by(book_id=old.book_id)
            .scalar()
        ) or 0

        new_summary = Summary(
            book_id=old.book_id,
            user_id=old.user_id,
            summary_text=old.summary_text,
            summary_length=old.summary_length,
            model_used=old.model_used,
            parameters=old.parameters,
            version=last_version + 1
        )

        db.session.add(new_summary)
        db.session.commit()

        return jsonify({"message": "Summary restored as new version"})

    return app

# -------------------- ENTRY POINT --------------------
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, use_reloader=False)
