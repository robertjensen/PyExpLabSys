from PyExpLabSys.drivers.xp_power_hpa_series import  XP_HPA_PS

class XP_HPT_PS(XP_HPA_PS):
    """
    This is a primitive driver for HPT that simply scales the voltage by
    a factor of 4 compared tp HPA. Later on we need to look into an actual
    driver update implemented according to specs
    """
    def __init__(self, i2c_address):
        super().__init__(i2c_address)

    def set_voltage(self, voltage):
        applied_v = voltage / 4.0
        super().set_voltage(applied_v)

    def read_actual_voltage(self):
        apparant_v = super().read_actual_voltage()
        actual_v = apparant_v * 4
        return actual_v
