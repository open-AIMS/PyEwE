class EwEError(Exception):

    def __init__(self, core_state, message):
        self._core_summary = core_state.non_model_summary()
        self.message = message
        super().__init__(message)

    def get_state(self):
        return self._core_summary

    def __str__(self):
        return f"{self.message} \n\n{self._core_summary}"


class EcopathError(EwEError):

    def __init__(self, core_state, message):
        self.message = message
        self._model_summary = core_state.ecosim_summary()
        super().__init__(core_state, message)


class EcosimError(EwEError):

    def __init__(self, core_state, message):
        self.message = message
        self._model_summary = core_state.ecosim_summary()
        super().__init__(core_state, message)

    def __str__(self):
        return f"{self.message} \n\n{self._model_summary}"


class EcotracerError(EwEError):

    def __init__(self, core_state, message):
        self.message = message
        self._model_summary = core_state.ecotracer_summary()
        super().__init__(core_state, message)

    def __str__(self):
        return f"{self.message} \n\n{super().get_state()}\n{self._model_summary}"


class EcosimNoScenarioError(EcosimError):

    def __init__(self, core_state):
        default_message = "No Ecosim scenario loaded. "
        default_message += "Call EcosimStateManager.load_scenario() to load a scenario."
        super().__init__(core_state, default_message)


class EcotracerNoScenarioError(EcotracerError):

    def __init__(self, core_state):
        default_message = "No Ecotracer scenario loaded. "
        default_message += (
            "Call EcotracerStateManager.load_scenario() to load a scenario."
        )
        super().__init__(core_state, default_message)
