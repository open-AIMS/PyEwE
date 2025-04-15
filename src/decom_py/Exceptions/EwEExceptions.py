class EwEError(Exception):

    def __init__(self, core_state, message):
        self._core_state = core_state.non_model_summary()
        super().__init__(message)


    def get_state(self):
        return self.core_summary

class EcopathError(EwEError):

    def __init__(self, core_state, message):
        self.message = message
        self._core_summary = core_state.ecosim_summary()
        super().__init__(core_state, message)

class EcosimError(EwEError):

    def __init__(self, core_state, message):
        self.message = message
        self._core_summary = core_state.ecosim_summary()
        super().__init__(core_state, message)

    def __str__(self):
        return f"{self.message} \n\n{self._core_summary}"

class EcotracerError(EwEError):

    def __init__(self, core_state, message):
        self.message = message
        self._core_summary = core_state.ecotracer_summary()
        super().__init__(core_state, message)

    def __str__(self):
        return f"{self.message} \n\n{super().get_state()}\n{self._core_summary}"
