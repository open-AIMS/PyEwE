def _format_property_line(property_name: str, val) -> str:
    return "{}: {}\n".format(property_name, val)


class EwEState:

    def __init__(self, core):
        self._monitor = core.StateMonitor

    def CanEcopathLoad(self) -> bool:
        return self._monitor.CanEcopathLoad()

    def CanEcosimLoad(self) -> bool:
        return self._monitor.CanEcosimLoad()

    def CanEcospaceLoad(self) -> bool:
        return self._monitor.CanEcospaceLoad()

    def CanEcotracerLoad(self) -> bool:
        return self._monitor.CanEcotracerLoad()

    def HasEcopathInitialized(self) -> bool:
        return self._monitor.HasEcopathInitialized()

    def HasEcopathLoaded(self) -> bool:
        return self._monitor.HasEcopathLoaded()

    def HasEcopathRan(self) -> bool:
        return self._monitor.HasEcopathRan()

    def HasEcosimInitialized(self) -> bool:
        return self._monitor.HasEcosimInitialized()

    def HasEcosimLoaded(self) -> bool:
        return self._monitor.HasEcosimLoaded()

    def HasEcosimRan(self) -> bool:
        return self._monitor.HasEcosimRan()

    def HasEcospaceInitialized(self) -> bool:
        return self._monitor.HasEcospaceInitialized()

    def HasEcospaceLoaded(self) -> bool:
        return self._monitor.HasEcospaceLoaded()

    def HasEcospaceRan(self) -> bool:
        return self._monitor.HasEcospaceRan()

    def HasEcotracerLoaded(self) -> bool:
        return self._monitor.HasEcotracerLoaded()

    def HasEcotracerRanForEcosim(self) -> bool:
        return self._monitor.HasEcotracerRanForEcosim()

    def HasEcotracerRanForEcospace(self) -> bool:
        return self._monitor.HasEcotracerRanForEcospace()

    def HasPSDRan(self) -> bool:
        return self._monitor.HasPSDRan()

    def IsBatchLocked(self) -> bool:
        return self._monitor.IsBatchLocked()

    def IsBusy(self) -> bool:
        return self._monitor.IsBusy()

    def IsDatasourceModified(self) -> bool:
        return self._monitor.IsDatasourceModified()

    def IsEcopathModified(self) -> bool:
        return self._monitor.IsEcopathModified()

    def IsEcopathRunning(self) -> bool:
        return self._monitor.IsEcopathRunning()

    def IsEcosimModified(self) -> bool:
        return self._monitor.IsEcosimModified()

    def IsEcosimRunning(self) -> bool:
        return self._monitor.IsEcosimRunning()

    def IsEcospaceModified(self) -> bool:
        return self._monitor.IsEcospaceModified()

    def IsEcospaceRunning(self) -> bool:
        return self._monitor.IsEcospaceRunning()

    def IsEcotracerModified(self) -> bool:
        return self._monitor.IsEcotracerModified()

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
