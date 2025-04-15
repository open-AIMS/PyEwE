import importlib
from types import MethodType
from functools import wraps, partial


def _format_property_line(property_name: str, val) -> str:
    return "{}: {}\n".format(property_name, val)


class EwEState:

    def __init__(self, core):
        self._monitor = core.StateMonitor

        # Auto-add monitor methods
        for method_name in dir(self._monitor):
            if not method_name.startswith('_'):
                # Only bind public methods
                method = getattr(self._monitor, method_name)
                if callable(method):
                    # Use functools.partial to bind the method
                    setattr(self, method_name, partial(getattr(self._monitor, method_name)))

    # This is the quick and dirty way of reflecting methods from StateMonitor.
    # It works, but reduces discoverability (e.g., tab-completion does not work)
    # def __getattr__(self, name):
    #     return getattr(self._monitor, name)
    
    def non_model_summary(self) -> str:
        summary = "---- EwE State ----\n"
        summary += _format_property_line("CanEcopathLoad", self.CanEcopathLoad())
        summary += _format_property_line("CanEcosimLoad", self.CanEcopathLoad())
        summary += _format_property_line("CanEcospaceLoad", self.CanEcopathLoad())
        summary += _format_property_line("CanEcotracerLoad" , self.CanEcopathLoad())
        return summary

    def print_non_model_summary(self) -> None:
        print(self.non_model_summary())

    def ecotracer_summary(self) -> str:
        summary = "---- EcoTracer State ----\n"
        summary += _format_property_line("HasEcotracerLoaded", self.HasEcotracerLoaded())
        summary += _format_property_line("HasEcotracerRanForEcosim", self.HasEcotracerRanForEcosim())
        summary += _format_property_line("HasEcotracerRanForEcospace", self.HasEcotracerRanForEcospace())
        summary += _format_property_line("IsEcotracerModified" , self.IsEcotracerModified())
        return summary

    def print_ecotracer_summary(self) -> None:
        print(self.ecotracer_summary())

    def ecosim_summary(self) -> str:
        summary = "---- Ecosim State ----\n"
        summary += _format_property_line("HasEcosimInitialized", self.HasEcosimInitialized())
        summary += _format_property_line("HasEcosimLoaded", self.HasEcosimLoaded())
        summary += _format_property_line("HasEcosimRan", self.HasEcosimRan())
        summary += _format_property_line("IsEcosimRunning", self.IsEcosimRunning())
        summary += _format_property_line("IsEcosimModified", self.IsEcosimModified())
        return summary

    def print_ecosim_summary(self) -> None:
        print(self.ecosim_summary())

    def ecopath_summary(self) -> str:
        summary = "---- Ecopath State ----\n"
        summary += _format_property_line("HasEcopathInitialized", self.HasEcopathInitialized())
        summary += _format_property_line("HasEcopathLoaded", self.HasEcopathLoaded())
        summary += _format_property_line("HasEcopathRan", self.HasEcopathRan())
        summary += _format_property_line("IsEcopathRunning", self.IsEcopathRunning())
        summary += _format_property_line("IsEcopathModified", self.IsEcopathModified())
        return summary

    def print_ecopath_summary(self) -> None:
        print(self.ecopath_summary())

    def summary(self) -> str:
        summary = "---- Complate State Summary ----\n"
        summary += self.non_model_summary() + "\n"
        summary += self.ecopath_summary() + "\n"
        summary += self.ecosim_summary() + "\n"
        summary += self.ecotracer_summary()
        return summary

    def print_summary(self) -> None:
        print(self.summary())
