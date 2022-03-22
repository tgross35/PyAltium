"""base.py

Base matlib types not really meant for direct use outside of source."""
import xml.etree.ElementTree as ET
from dataclasses import KW_ONLY, dataclass, field
from datetime import datetime
from typing import Callable
from uuid import UUID, uuid4

from pyaltium.helpers import REALNUM, dehumanize, humanize, load_dt, safe_uuid
from pyaltium.matlib.helpers import HEX_ALPHA_REGEX, MatLibTypeID


class PropertyValidationError(Exception):
    """Raised when a property does not meet requirements."""

    pass


@dataclass
class MatProperty:
    """Holds information about a Property, a subclass of Entity for materials library."""

    name: str
    type: str
    value: str
    attrib: dict[str, str] = field(default_factory=dict)
    validator: Callable = None
    validator_message: str = ""
    atrset: str = ""
    setproc: Callable = field(default=lambda x: x)

    def _get_xml(self):
        """Validate value then return an XML element."""
        if self.validator:
            if not self.__class__.validator(self.value):
                raise PropertyValidationError(self.validator_message)

        prop = ET.Element("Property")
        prop.set("Name", str(self.name))
        prop.set("Type", str(self.type))
        [prop.set(k, str(v)) for k, v in self.attrib.items()]
        prop.text = str(self.value)
        return prop


@dataclass
class ColorProperty(MatProperty):
    """More specific version of a MatProperty, specifically for colors"""

    _: KW_ONLY
    name: str = field(default="Color", init=False)
    type: str = field(
        default="System.Windows.Media.Color, PresentationCore, Version=4.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35",
        init=False,
    )
    attrib: dict[str, str] = field(default_factory=dict, init=False)
    validator: Callable = field(default=lambda x: HEX_ALPHA_REGEX.match(x), init=False)
    validator_message: str = field(
        default="Color needs to be in the format #abababab (hex plus alpha)", init=False
    )


@dataclass
class MatLibEntity:
    """Base class to represent a single item"""

    type_id: MatLibTypeID = field(init=False)
    entity_id: UUID = field(default_factory=uuid4, init=False)
    revision_id: UUID = field(default_factory=uuid4, init=False)
    revision_date: datetime = field(default_factory=datetime.utcnow, init=False)

    def _load(self, x: ET.Element) -> None:
        """Load in a XML Element to populate class data."""
        self.entity_id = safe_uuid(x.attrib.get("Id"))
        self.type_id = MatLibTypeID(safe_uuid(x.attrib.get("TypeId")))
        self.revision_id = safe_uuid(x.attrib.get("RevisionId"))
        self.revision_date = load_dt(x.attrib.get("RevisionDate"))
        selfprops = self._get_properties()

        for xmlprop in x.iter("Property"):
            name = xmlprop.attrib.get("Name")
            prop: MatProperty = next(filter(lambda p: p.name == name, selfprops))
            if prop:
                val = prop.setproc(xmlprop.text)
                setattr(self, prop.atrset, val)

    def _get_properties(self) -> list[MatProperty]:
        """Return a list of properties in XML format.

        :raises NotImplementedError: Method not properly overridden
        :return: List of properties
        :rtype: list[MatProperty]
        """
        raise NotImplementedError

    def _get_xml(self) -> ET.Element:
        entity = ET.Element("Entity")
        entity.set("Id", str(self.entity_id))
        entity.set("TypeId", str(self.type_id.value))
        entity.set("RevisionId", str(self.revision_id))

        formatted_date = self.revision_date.isoformat().replace("+00:00", "Z")
        entity.set("RevisionDate", f"{formatted_date}")

        [entity.append(p._get_xml()) for p in self._get_properties()]
        return entity


@dataclass
class DielectricBase(MatLibEntity):
    """Base class used for all dielectrics, with common elements.

    Construction: e.g. 2113 or 1-2113
    Resin: A percent, 0-100
    Glass temp: glass transistion temp in celsius"""

    name: str = ""
    dielectric_constant: REALNUM = 0
    thickness: REALNUM = 0
    glass_trans_temp: REALNUM = 0
    manufacturer: str = ""
    construction: str = ""
    resin_pct: REALNUM = 0
    frequency: REALNUM = 0
    loss_tangent: REALNUM = 0

    def _get_properties(self) -> list[MatProperty]:
        return [
            MatProperty(
                "Constructions", "String", self.construction, atrset="construction"
            ),
            MatProperty(
                "Resin",
                "DimValue",
                f"{self.resin_pct}%",
                {"Dimension": "Relative"},
                atrset="resin_pct",
                setproc=lambda x: float(x.replace("%", "")),
            ),
            MatProperty(
                "Frequency",
                "DimValue",
                humanize(self.frequency, "Hz", False),
                {"Dimension": "Frequency"},
                atrset="frequency",
                setproc=lambda x: dehumanize(x, "Hz"),
            ),
            MatProperty(
                "DielectricConstant",
                "DimValue",
                self.dielectric_constant,
                {"Dimension": "Dimensionless"},
                atrset="dielectric_constant",
            ),
            MatProperty(
                "LossTangent",
                "DimValue",
                self.loss_tangent,
                {"Dimension": "Dimensionless"},
                atrset="loss_tangent",
            ),
            MatProperty(
                "GlassTransTemp",
                "DimValue",
                f"{self.glass_trans_temp}C",
                {"Dimension": "Temperature"},
                atrset="glass_trans_temp",
            ),
            MatProperty(
                "Manufacturer", "String", self.manufacturer, atrset="manufacturer"
            ),
            MatProperty("Name", "String", self.name, atrset="name"),
            MatProperty(
                "Thickness",
                "DimValue",
                f"{self.thickness}mm",
                {"Dimension": "Length"},
                atrset="thickness",
            ),
        ]


@dataclass
class FinishBase(MatLibEntity):
    """Base class used for all finishes, with common elements."""

    process: str = ""
    material: str = ""
    thickness: REALNUM = 0
    color: str = "#ffffffff"

    def _get_properties(self) -> list[MatProperty]:
        return [
            MatProperty(
                "Thickness",
                "DimValue",
                f"{self.thickness}mm",
                {"Dimension": "Length"},
            ),
            MatProperty("Process", "String", self.process),
            MatProperty("Material", "String", self.material),
            ColorProperty(self.color),
        ]