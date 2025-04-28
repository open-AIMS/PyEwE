# Net arrays to numpy arrays was taken from the following discussion on github
# https://github.com/pythonnet/pythonnet/issues/514#issuecomment-350375105

from System.Reflection import BindingFlags
import numpy as np
import ctypes
import clr, System
from System import Array, Int32
from System.Runtime.InteropServices import GCHandle, GCHandleType
from .Exceptions import EcopathError, EcotracerError, EcosimError

from .EwEState import EwEState

_MAP_NP_NET = {
    np.dtype('float32'): System.Single,
    np.dtype('float64'): System.Double,
    np.dtype('int8')   : System.SByte,
    np.dtype('int16')  : System.Int16,
    np.dtype('int32')  : System.Int32,
    np.dtype('int64')  : System.Int64,
    np.dtype('uint8')  : System.Byte,
    np.dtype('uint16') : System.UInt16,
    np.dtype('uint32') : System.UInt32,
    np.dtype('uint64') : System.UInt64,
    np.dtype('bool')   : System.Boolean,
}
_MAP_NET_NP = {
    'Single' : np.dtype('float32'),
    'Double' : np.dtype('float64'),
    'SByte'  : np.dtype('int8'),
    'Int16'  : np.dtype('int16'),
    'Int32'  : np.dtype('int32'),
    'Int64'  : np.dtype('int64'),
    'Byte'   : np.dtype('uint8'),
    'UInt16' : np.dtype('uint16'),
    'UInt32' : np.dtype('uint32'),
    'UInt64' : np.dtype('uint64'),
    'Boolean': np.dtype('bool'),
}

def intoNumpyArray(netArray, buffer):
    '''
    Given a CLR `System.Array` returns a `numpy.ndarray`.  See _MAP_NET_NP for
    the mapping of CLR types to Numpy dtypes.
    '''
    dims = np.empty(netArray.Rank, dtype=int)
    for I in range(netArray.Rank):
        dims[I] = netArray.GetLength(I)

    if not all(i == j for (i, j) in zip(dims, buffer.shape)):
        msg = f"Attempting to copy a .NET array of shape {dims} "
        msg += f"into a numpy.ndarray of shape {buffer.shape}"
        raise RuntimeError(msg)

    try: # Memmove
        sourceHandle = GCHandle.Alloc(netArray, GCHandleType.Pinned)
        sourcePtr = sourceHandle.AddrOfPinnedObject().ToInt64()
        destPtr = buffer.__array_interface__['data'][0]
        ctypes.memmove(destPtr, sourcePtr, buffer.nbytes)
    finally:
        if sourceHandle.IsAllocated: sourceHandle.Free()
    return buffer

def asNumpyArray(netArray):
    """
    Given a CLR `System.Array` returns a `numpy.ndarray`.  See _MAP_NET_NP for
    the mapping of CLR types to Numpy dtypes.
    """
    dims = np.empty(netArray.Rank, dtype=int)
    for I in range(netArray.Rank):
        dims[I] = netArray.GetLength(I)
    netType = netArray.GetType().GetElementType().Name

    try:
        npArray = np.empty(dims, order='C', dtype=_MAP_NET_NP[netType])
    except KeyError:
        raise NotImplementedError("asNumpyArray does not yet support System type {}".format(netType) )

    try: # Memmove
        sourceHandle = GCHandle.Alloc(netArray, GCHandleType.Pinned)
        sourcePtr = sourceHandle.AddrOfPinnedObject().ToInt64()
        destPtr = npArray.__array_interface__['data'][0]
        ctypes.memmove(destPtr, sourcePtr, npArray.nbytes)
    finally:
        if sourceHandle.IsAllocated: sourceHandle.Free()
    return npArray

class ResultStoreEnum:
    """Enum for Core result private fields."""
    ECOPATH: str = "m_EcopathData"
    ECOSIM: str = "m_EcoSimData"
    ECOTRACER: str = "m_tracerData"

class ResultExtractor:
    """A base class to extract result variables from private core result objects.

    The results extraction class maintains a buffer the size of the variable being extracted
    and manages access to the non-public core field. It uses a straight memory copy of the
    underlying net array to a numpy array buffer that is reused during its lifetime.

    Attributes:
        core: EwE core instance to extract data from.
        private_field: name of the non-public field to access.
        array_name: name of the array in the non-public field.
    """

    def __init__(
        self,
        core,
        monitor: EwEState,
        private_field: str,
        array_name: str
    ):
        self._core = core
        self._monitor = monitor
        self._private_field = private_field
        self._array_name = array_name
        self._buffer = None

        flags = BindingFlags.Instance | BindingFlags.NonPublic
        obj_type = self._core.GetType()
        self._private_field_info = obj_type.GetField(private_field, flags)

    def _has_run_check(self):
        if self._private_field == ResultStoreEnum.ECOPATH:
            raise EcopathError(
                self._monitor, "Ecopath must be run before accessing results."
            )
        elif self._private_field == ResultStoreEnum.ECOSIM:
            raise EcosimError(
                self._monitor, "Ecosim must be run before accessing results."
            )
        elif self._private_field == ResultStoreEnum.ECOTRACER:
            raise EcotracerError(
                self._monitor, "Ecotracer must be run before accessing results."
            )
        else:
            raise ValueError(f"{self._private_field} is not a valid non-public field name.")


    def _get_dot_net_array(self):
        return getattr(self._private_field_info.GetValue(self._core), self._array_name)

    def refresh_buffer(self):
        self._has_run_check()
        if self._buffer is None:
            # allocate and write buffer
            self._buffer = asNumpyArray(self._get_dot_net_array())
        else:
            intoNumpyArray(self._get_dot_net_array(), self._buffer)

    def _get_buffer(self):
        if self._buffer is None:
            raise RuntimeError("Buffer has not been allocated prior to result extraction.")

        return self._buffer

class SingleResultsExtractor(ResultExtractor):
    """A result extraction class that handles the extraction of a single variable. 

    Attributes:
        core: Instance of the EwE core to extract results from.
        private_field: name of the private field to access.
        array_name: name of the array in the private field to access.
    """

    def __init__(
        self,
        core,
        monitor: EwEState,
        private_field: str,
        array_name: str
    ):
        super().__init__(core, monitor, private_field, array_name)

    def get_result(self):
        """Get the numpy.ndarray containing the results."""
        return self._get_buffer()

class PackedResultsExtractor(ResultExtractor):

    def __init__(
        self,
        core,
        monitor,
        private_field: str,
        array_name: str,
        variable_map: dict[str, int]
    ):
        super().__init__(core, monitor, private_field, array_name)
        self._variable_map = variable_map

    def get_result(self, variable_name: str):
        """Get the numpy.ndarray containing the results of the given variable."""
        return self._get_buffer()[self._variable_map[variable_name]]

def create_ecosim_group_stats_extractors(core, monitor):
    """Create an extractor for the EcoSim group statistics results."""
    return PackedResultsExtractor(
        core,
        monitor,
        ResultStoreEnum.ECOSIM,
        "ResultsOvertime",
        {
            "Biomass":         0,
            "BiomassRel":      1,
            "Yield":           2,
            "YieldRel":        3,
            "FeedingTime":     4,
            "ConsumpBiomass":  5,
            "TotalMort":       6,
            "PredMort":        7,
            "FishMort":        8,
            "ProdConsump":     9,
            "AvgWeight":       10,
            "MortVPred":       11,
            "MortVFishing":    12,
            "EcoSysStructure": 13,
            "TL":              14
        }
    )

def create_conc_extractor(core, monitor):
    """Create an extractor for the Ecotracer concentration results."""
    return SingleResultsExtractor(core, monitor, ResultStoreEnum.ECOTRACER, "TracerConc")

def create_conc_biomass_extractor(core, monitor):
    """Create an extractor for the Ecotracer concentration overbiomass results."""
    return SingleResultsExtractor(core, monitor, ResultStoreEnum.ECOTRACER, "TracerCB")

def create_TL_catch_extractor(core, monitor):
    """Create an extractor for the Ecosim trophic level catch results."""
    return SingleResultsExtractor(core, monitor, ResultStoreEnum.ECOSIM, "TLC")

def create_FIB_extractor(core, monitor):
    """Create an extractor for the Ecosim FIB results."""
    return SingleResultsExtractor(core, monitor, ResultStoreEnum.ECOSIM, "FIB")

def create_Kemptons_extractor(core, monitor):
    """Create an extractor for the Ecosim Kempton results."""
    return SingleResultsExtractor(core, monitor, ResultStoreEnum.ECOSIM, "Kemptons")

def create_shannon_diversity_extractor(core, monitor):
    """Create an extractor for the Ecosim Shannon Diversity results."""
    return SingleResultsExtractor(core, monitor, ResultStoreEnum.ECOSIM, "ShannonDiversity")
