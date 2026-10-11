from __future__ import annotations

from sqlalchemy import Engine, ForeignKey, Integer, String, Text, UniqueConstraint, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

from app.domain.tipos import TipoEntidad, TipoRelacion
from app.persistence.database import session_scope
from app.persistence.errors import SchemaInitializationError


class Base(DeclarativeBase):
    pass


class TipoEntidadModel(Base):
    __tablename__ = "tipo_entidad"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(String(128), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)

    entidades: Mapped[list[EntidadModel]] = relationship(back_populates="tipo_entidad")


class EntidadModel(Base):
    __tablename__ = "entidad"
    __table_args__ = (
        UniqueConstraint(
            "tipo_entidad_id",
            "valor_normalizado",
            name="uq_entidad_tipo_valor_normalizado",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tipo_entidad_id: Mapped[int] = mapped_column(
        ForeignKey("tipo_entidad.id", ondelete="RESTRICT"),
        nullable=False,
    )
    valor: Mapped[str] = mapped_column(Text, nullable=False)
    valor_normalizado: Mapped[str] = mapped_column(Text, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column("metadata", Text, nullable=True)

    tipo_entidad: Mapped[TipoEntidadModel] = relationship(back_populates="entidades")
    relaciones_origen: Mapped[list[RelacionModel]] = relationship(
        back_populates="origen",
        foreign_keys="RelacionModel.origen_id",
        passive_deletes=True,
    )
    relaciones_destino: Mapped[list[RelacionModel]] = relationship(
        back_populates="destino",
        foreign_keys="RelacionModel.destino_id",
        passive_deletes=True,
    )


class TipoRelacionModel(Base):
    __tablename__ = "tipo_relacion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(String(128), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)

    relaciones: Mapped[list[RelacionModel]] = relationship(back_populates="tipo_relacion")


class RelacionModel(Base):
    __tablename__ = "relacion"
    __table_args__ = (
        UniqueConstraint(
            "origen_id",
            "destino_id",
            "tipo_relacion_id",
            name="uq_relacion_origen_destino_tipo",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    origen_id: Mapped[int] = mapped_column(ForeignKey("entidad.id", ondelete="CASCADE"), nullable=False)
    destino_id: Mapped[int] = mapped_column(
        ForeignKey("entidad.id", ondelete="CASCADE"),
        nullable=False,
    )
    tipo_relacion_id: Mapped[int] = mapped_column(
        ForeignKey("tipo_relacion.id", ondelete="RESTRICT"),
        nullable=False,
    )
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha: Mapped[str | None] = mapped_column(String(64), nullable=True)

    origen: Mapped[EntidadModel] = relationship(
        back_populates="relaciones_origen",
        foreign_keys=[origen_id],
    )
    destino: Mapped[EntidadModel] = relationship(
        back_populates="relaciones_destino",
        foreign_keys=[destino_id],
    )
    tipo_relacion: Mapped[TipoRelacionModel] = relationship(back_populates="relaciones")
    evidencias: Mapped[list[EvidenciaModel]] = relationship(
        back_populates="relacion",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class EvidenciaModel(Base):
    __tablename__ = "evidencia"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    relacion_id: Mapped[int] = mapped_column(
        ForeignKey("relacion.id", ondelete="CASCADE"),
        nullable=False,
    )
    fuente: Mapped[str] = mapped_column(Text, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha: Mapped[str | None] = mapped_column(String(64), nullable=True)

    relacion: Mapped[RelacionModel] = relationship(back_populates="evidencias")


ENTITY_TYPE_SEED: tuple[tuple[str, str, str | None], ...] = (
    (TipoEntidad.PERSONA.value, "Persona", "Entidad de tipo persona."),
    (TipoEntidad.ORGANIZACION.value, "Organización", "Entidad de tipo organización."),
    (TipoEntidad.EMAIL.value, "Email", "Entidad de tipo email."),
    (TipoEntidad.USUARIO.value, "Usuario", "Entidad de tipo usuario."),
    (TipoEntidad.DOMINIO.value, "Dominio", "Entidad de tipo dominio."),
    (TipoEntidad.SITIO_WEB.value, "Sitio web", "Entidad de tipo sitio web."),
    (TipoEntidad.IP.value, "IP", "Entidad de tipo dirección IP."),
)

RELATION_TYPE_SEED: tuple[tuple[str, str, str | None], ...] = (
    (TipoRelacion.POSEE.value, "Posee", "Relación de posesión."),
    (TipoRelacion.UTILIZA.value, "Utiliza", "Relación de utilización."),
    (TipoRelacion.TRABAJA_EN.value, "Trabaja en", "Relación laboral."),
    (TipoRelacion.ADMINISTRA.value, "Administra", "Relación de administración."),
    (TipoRelacion.PERTENECE_A.value, "Pertenece a", "Relación de pertenencia."),
    (TipoRelacion.APUNTA_A.value, "Apunta a", "Relación de dirección o referencia."),
)


def create_schema(engine: Engine) -> None:
    try:
        Base.metadata.create_all(bind=engine)
    except SQLAlchemyError as exc:
        raise SchemaInitializationError("No se pudo crear el esquema de persistencia.") from exc


def seed_catalogs(session: Session) -> None:
    existing_entity_codes = set(session.scalars(select(TipoEntidadModel.codigo)).all())
    for code, name, description in ENTITY_TYPE_SEED:
        if code in existing_entity_codes:
            continue
        session.add(TipoEntidadModel(codigo=code, nombre=name, descripcion=description))

    existing_relation_codes = set(session.scalars(select(TipoRelacionModel.codigo)).all())
    for code, name, description in RELATION_TYPE_SEED:
        if code in existing_relation_codes:
            continue
        session.add(TipoRelacionModel(codigo=code, nombre=name, descripcion=description))


def initialize_database(engine: Engine, session_factory: sessionmaker[Session]) -> None:
    create_schema(engine)
    try:
        with session_scope(session_factory) as session:
            seed_catalogs(session)
    except SQLAlchemyError as exc:
        raise SchemaInitializationError(
            "No se pudo inicializar la base de datos con los catálogos iniciales."
        ) from exc

