from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

GIS_SCHEMA = "gis"


class Building(Base):
    __tablename__ = "building"
    __table_args__ = {"schema": GIS_SCHEMA}

    building_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(String(500))
    center_lat: Mapped[Decimal | None] = mapped_column(Numeric(10, 8))
    center_lng: Mapped[Decimal | None] = mapped_column(Numeric(11, 8))
    total_floors: Mapped[int | None] = mapped_column(Integer)
    arcgis_layer_id: Mapped[str | None] = mapped_column(String(100))

    floors: Mapped[list[Floor]] = relationship(back_populates="building")
    cell_spaces: Mapped[list[CellSpace]] = relationship(back_populates="building")


class Floor(Base):
    __tablename__ = "floor"
    __table_args__ = {"schema": GIS_SCHEMA}

    floor_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    building_id: Mapped[int] = mapped_column(
        ForeignKey(
            f"{GIS_SCHEMA}.building.building_id",
            name="fk_gis_floor_building_id_building",
        ),
        nullable=False,
    )
    floor_number: Mapped[int | None] = mapped_column(Integer)
    floor_name: Mapped[str | None] = mapped_column(String(100))
    altitude_min: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    altitude_max: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    building: Mapped[Building] = relationship(back_populates="floors")
    cell_spaces: Mapped[list[CellSpace]] = relationship(back_populates="floor")


class CellSpace(Base):
    __tablename__ = "cell_space"
    __table_args__ = {"schema": GIS_SCHEMA}

    cell_space_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    floor_id: Mapped[int] = mapped_column(
        ForeignKey(
            f"{GIS_SCHEMA}.floor.floor_id",
            name="fk_gis_cell_space_floor_id_floor",
        ),
        nullable=False,
    )
    building_id: Mapped[int] = mapped_column(
        ForeignKey(
            f"{GIS_SCHEMA}.building.building_id",
            name="fk_gis_cell_space_building_id_building",
        ),
        nullable=False,
    )
    name: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(String(500))
    center_lat: Mapped[Decimal | None] = mapped_column(Numeric(10, 8))
    center_lng: Mapped[Decimal | None] = mapped_column(Numeric(11, 8))
    total_floors: Mapped[int | None] = mapped_column(Integer)
    arcgis_layer_id: Mapped[str | None] = mapped_column(String(100))

    floor: Mapped[Floor] = relationship(back_populates="cell_spaces")
    building: Mapped[Building] = relationship(back_populates="cell_spaces")
    boundaries: Mapped[list[CellSpaceBoundary]] = relationship(back_populates="cell_space")
    geofence_rules: Mapped[list[GeofenceRule]] = relationship(back_populates="cell_space")
    gis_layers: Mapped[list[GisLayer]] = relationship(back_populates="cell_space")
    states: Mapped[list[State]] = relationship(back_populates="cell_space")


class CellSpaceBoundary(Base):
    __tablename__ = "cell_space_boundary"
    __table_args__ = {"schema": GIS_SCHEMA}

    boundary_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cell_space_id: Mapped[int] = mapped_column(
        ForeignKey(
            f"{GIS_SCHEMA}.cell_space.cell_space_id",
            name="fk_gis_cell_space_boundary_cell_space_id_cell_space",
        ),
        nullable=False,
    )
    boundary_type: Mapped[str | None] = mapped_column(String(100))
    boundary_geometry_type: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)

    cell_space: Mapped[CellSpace] = relationship(back_populates="boundaries")


class GeofenceRule(Base):
    __tablename__ = "geofence_rule"
    __table_args__ = {"schema": GIS_SCHEMA}

    geofence_rule_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cell_space_id: Mapped[int] = mapped_column(
        ForeignKey(
            f"{GIS_SCHEMA}.cell_space.cell_space_id",
            name="fk_gis_geofence_rule_cell_space_id_cell_space",
        ),
        nullable=False,
    )
    allowed_radius_m: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    altitude_min: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    altitude_max: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    allow_checkin: Mapped[bool | None] = mapped_column(Boolean)
    allow_checkout: Mapped[bool | None] = mapped_column(Boolean)
    is_active: Mapped[bool | None] = mapped_column(Boolean)
    created_by_account_id: Mapped[int | None] = mapped_column(Integer)

    cell_space: Mapped[CellSpace] = relationship(back_populates="geofence_rules")
    attendance_records: Mapped[list[AttendanceRecord]] = relationship(back_populates="geofence_rule")


class GisLayer(Base):
    __tablename__ = "gis_layer"
    __table_args__ = {"schema": GIS_SCHEMA}

    layer_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cell_space_id: Mapped[int] = mapped_column(
        ForeignKey(
            f"{GIS_SCHEMA}.cell_space.cell_space_id",
            name="fk_gis_gis_layer_cell_space_id_cell_space",
        ),
        nullable=False,
    )
    arcgis_layer_id: Mapped[str | None] = mapped_column(String(100))
    layer_type: Mapped[str | None] = mapped_column(String(100))
    layer_url: Mapped[str | None] = mapped_column(Text)
    is_visible: Mapped[bool | None] = mapped_column(Boolean)

    cell_space: Mapped[CellSpace] = relationship(back_populates="gis_layers")


class State(Base):
    __tablename__ = "state"
    __table_args__ = {"schema": GIS_SCHEMA}

    state_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cell_space_id: Mapped[int] = mapped_column(
        ForeignKey(
            f"{GIS_SCHEMA}.cell_space.cell_space_id",
            name="fk_gis_state_cell_space_id_cell_space",
        ),
        nullable=False,
    )
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 8))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(11, 8))
    altitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    state_type: Mapped[str | None] = mapped_column(String(100))

    cell_space: Mapped[CellSpace] = relationship(back_populates="states")
    outgoing_transitions: Mapped[list[Transition]] = relationship(
        back_populates="from_state",
        foreign_keys="Transition.from_state_id",
    )
    incoming_transitions: Mapped[list[Transition]] = relationship(
        back_populates="to_state",
        foreign_keys="Transition.to_state_id",
    )


class Transition(Base):
    __tablename__ = "transition"
    __table_args__ = {"schema": GIS_SCHEMA}

    transition_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    from_state_id: Mapped[int] = mapped_column(
        ForeignKey(
            f"{GIS_SCHEMA}.state.state_id",
            name="fk_gis_transition_from_state_id_state",
        ),
        nullable=False,
    )
    to_state_id: Mapped[int] = mapped_column(
        ForeignKey(
            f"{GIS_SCHEMA}.state.state_id",
            name="fk_gis_transition_to_state_id_state",
        ),
        nullable=False,
    )
    transition_type: Mapped[str | None] = mapped_column(String(100))
    distance_m: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    from_state: Mapped[State] = relationship(
        back_populates="outgoing_transitions",
        foreign_keys=[from_state_id],
    )
    to_state: Mapped[State] = relationship(
        back_populates="incoming_transitions",
        foreign_keys=[to_state_id],
    )
