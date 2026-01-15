# This is a sample Python script.

# Press Ctrl+F5 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import secsgem.gem
import secsgem.hsms.settings
import secsgem.secs
import secsgem.common
import code

class SampleEquipment(secsgem.gem.GemEquipmentHandler):
    def __init__(self, settings: secsgem.common.Settings):
        super().__init__(settings)


        self.MDLN = "Eulitha"
        self.SOFTREV = "1.0.0"

        self.sv1 = 123
        self.sv2 = "sample sv"

        self.status_variables.update({
            10: secsgem.gem.StatusVariable(10, "sample1, numeric SVID, U4", "meters", secsgem.secs.variables.U4),
            "SV2": secsgem.gem.StatusVariable("SV2", "sample2, text SVID, String", "chars", secsgem.secs.variables.String),
        })

        self.ec1 = 321
        self.ec2 = "sample ec"

        self.equipment_constants.update({
            20: secsgem.gem.EquipmentConstant(20, "sample1, numeric ECID, U4", 0, 500, 50, "degrees", secsgem.secs.variables.U4),
            "EC2": secsgem.gem.EquipmentConstant("EC2", "sample2, text ECID, String", 0, 0, 0, "chars", secsgem.secs.variables.String),
        })







def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press F9 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

    settings = secsgem.hsms.HsmsSettings(
        address="127.0.0.1",
        port=5000,
        connect_mode=secsgem.hsms.HsmsConnectMode.PASSIVE,
        device_type=secsgem.common.DeviceType.EQUIPMENT
    )

    h = SampleEquipment(settings)
    h.enable()
    print(1)
    try:
        h.waitfor_communicating()
    except Exception as err:
        print(err)
    print(2)

    h.are_you_there()

    code.interact("equipment object is available as variable 'h', press ctrl-d to stop", local=locals())




    h.disable()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
