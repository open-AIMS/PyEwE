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

    def print_non_model_summary(self) -> None:
        summary = "---- EwE State ----\n"
        summary += _format_property_line("CanEcopathLoad", self.CanEcopathLoad())
        summary += _format_property_line("CanEcosimLoad", self.CanEcopathLoad())
        summary += _format_property_line("CanEcospaceLoad", self.CanEcopathLoad())
        summary += _format_property_line("CanEcotracerLoad" , self.CanEcopathLoad())
        print(summary)

    def print_ecotracer_summary(self) -> None:
        summary = "---- EcoTracer State ----\n"
        summary += _format_property_line("HasEcotracerLoaded", self.HasEcotracerLoaded())
        summary += _format_property_line("HasEcotracerRanForEcosim", self.HasEcotracerRanForEcosim())
        summary += _format_property_line("HasEcotracerRanForEcospace", self.HasEcotracerRanForEcospace())
        summary += _format_property_line("IsEcotracerModified" , self.IsEcotracerModified())
        print(summary)

    def print_ecosim_summary(self) -> None:
        summary = "---- Ecosim State ----\n"
        summary += _format_property_line("HasEcosimInitialized", self.HasEcosimInitialized())
        summary += _format_property_line("HasEcosimLoaded", self.HasEcosimLoaded())
        summary += _format_property_line("HasEcosimRan", self.HasEcosimRan())
        summary += _format_property_line("IsEcosimRunning", self.IsEcosimRunning())
        summary += _format_property_line("IsEcosimModified", self.IsEcosimModified())
        print(summary)

    def print_ecopath_summary(self) -> None:
        summary = "---- Ecopath State ----\n"
        summary += _format_property_line("HasEcopathInitialized", self.HasEcopathInitialized())
        summary += _format_property_line("HasEcopathLoaded", self.HasEcopathLoaded())
        summary += _format_property_line("HasEcopathRan", self.HasEcopathRan())
        summary += _format_property_line("IsEcopathRunning", self.IsEcopathRunning())
        summary += _format_property_line("IsEcopathModified", self.IsEcopathModified())
        print(summary)

    def print_summary(self) -> None:
        print("---- Complate State Summary ----\n")
        self.print_non_model_summary()
        self.print_ecopath_summary()
        self.print_ecosim_summary()
        self.print_ecotracer_summary()
