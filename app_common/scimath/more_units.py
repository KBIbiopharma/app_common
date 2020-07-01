""" More units.
"""
import sys
import logging
from copy import copy

from scimath.units import dimensionless, substance, volume, mass, length, \
    electromagnetism, time
from scimath.units.api import unit_parser

logger = logging.getLogger(__name__)


fraction = dimensionless.fraction

#: time
minute = time.minute
minute.label = 'min'

#: volume
milliliter = volume.liter * 1e-3
milliliter.label = 'mL'

#: concentration units
molar = substance.mole / volume.liter
molar.label = 'moles per liter'

milli_molar = molar * 1e-3
milli_molar.label = 'mmol/L'
milli_molar_mM = copy(milli_molar)
milli_molar_mM.label = 'mM'

gram_per_liter = mass.g / volume.liter
gram_per_liter.label = 'g/L'

gram_per_milliliter = mass.g / milliliter
gram_per_milliliter.label = 'g/mL'

kg_per_liter = mass.kg / volume.liter
kg_per_liter.label = 'kg/L'

#: fraction units
assay_unit = copy(fraction)
assay_unit.label = '%'

#: porosity units
porosity = 1 * fraction

#: absorption units
absorption_unit = 1 * fraction
absorption_unit.label = 'AU'

milli_absorption_unit = 1e-3 * fraction
milli_absorption_unit.label = 'mAU'

#: product extinction coefficient unit
#: (see wiki on uv visible spectroscopy)
extinction_coefficient_unit = (
    absorption_unit * volume.liter / (length.cm * mass.g)
)
extinction_coefficient_unit.label = "(AU * L)/(cm * g)"

#: atomic (molecular) weight
gram_per_mol = mass.g / substance.mole
gram_per_mol.label = 'g/mol'

dalton = copy(gram_per_mol)
dalton.label = "Da"

kilogram_per_mol = mass.kg / substance.mole
kilogram_per_mol.label = 'kg/mol'

kilo_dalton = copy(kilogram_per_mol)
kilo_dalton.label = "kDa"

#: conductivity
mS_per_cm = electromagnetism.mSiemen / length.cm
mS_per_cm.label = 'mS/cm'

#: Flow rates
cm_per_hr = length.cm / time.hour
cm_per_hr.label = "cm/hr"

ml_per_min = milliliter / time.minute
ml_per_min.label = 'mL/min'

#: column volumes
column_volumes = 1.0 * dimensionless.dimensionless
column_volumes.label = 'CV'

#: Volume of load is typically in gram per liter of resin
# To convert to volume in CV, divide by the product concentration in g/L
g_per_liter_resin = 1.0 * dimensionless.dimensionless
g_per_liter_resin.label = "g/Liter_resin"


def convert_g_per_liter_resin_to_cv(unitted_data, **kwargs):
    """ To convert to volume in CV, divide by the product concentration in g/L.
    """
    from .units_utils import convert_units

    if "concentration" not in kwargs:
        msg = "Trying to convert a volume in 'g per liter of resin' " \
              "requires a product concentration, but 'concentration' was" \
              " not found in the function keyword arguments."
        logger.exception(msg)
        raise ValueError(msg)

    concentration = kwargs["concentration"]
    concentration = convert_units(concentration, tgt_unit="g/L")
    return unitted_data / float(concentration)


def convert_cv_to_g_per_liter_resin(unitted_data, **kwargs):
    """ To convert to volume in g/L, multiply by product concentration in CV.
    """
    from .units_utils import convert_units

    if "concentration" not in kwargs:
        msg = "Trying to convert a volume in 'g per liter of resin' " \
              "requires a product concentration, but 'concentration' was" \
              " not found in the function keyword arguments."
        logger.exception(msg)
        raise ValueError(msg)

    concentration = kwargs["concentration"]
    concentration = convert_units(concentration, tgt_unit="g/L")
    return unitted_data * float(concentration)


CUSTOM_UNITS_CONVERTERS = {
    (g_per_liter_resin.label, column_volumes.label):
        convert_g_per_liter_resin_to_cv,
    (column_volumes.label, g_per_liter_resin.label):
        convert_cv_to_g_per_liter_resin,
}


current_module = sys.modules[__name__]
unit_parser.parser.extend(current_module)
