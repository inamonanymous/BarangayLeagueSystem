from types import TracebackType

from app.extensions import db


class SqlAlchemyUnitOfWork:
    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        committed = False
        try:
            if exc_type is None:
                db.session.commit()
                committed = True
        finally:
            if not committed:
                db.session.rollback()
