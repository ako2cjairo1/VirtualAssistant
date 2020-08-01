from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from ctypes import cast, POINTER
from argparse import ArgumentParser


class SysVolume:

    def __init__(self):
        self.volume = None

    def system_volume(self, vol):
        try:
            if vol:
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self.volume = cast(interface, POINTER(IAudioEndpointVolume))

                current_volume_level = self.volume.GetMasterVolumeLevel()

                if "+" in vol:
                    value = int(vol.replace("+", "")) * -3
                    value = float(current_volume_level + value)

                elif "-" in vol:
                    value = int(vol.replace("-", "")) * -3
                    value = float(current_volume_level - value)

                elif vol.isdigit():
                    value = int(vol)
                    value = float(-30 + (value * 3))

                # ensure value in range
                if value > 0.0:
                    value = 0.0		# 0%
                elif value < -30.0:
                    value = -30.0 	# 100%

                # volume.GetMute()
                # volume.GetVolumeRange()
                # volume range:
                # max: 0.0
                # min: -65.25
                self.volume.SetMasterVolumeLevel(value, None)
                return str(((self.volume.GetMasterVolumeLevel() / -30) * 100) // 10)

        except Exception as ex:
            raise Exception(f"SYSTEM VOLUME LIBRARY Encountered an Error. {str(ex)}")


if __name__ == "__main__":
    parser = ArgumentParser(description="Set System Volume.")
    # add option argument
    parser.add_argument("--volume", action="store", dest="volume", required=True, help="Numeric value of volume to set.")

    # parse parameter value(s)
    param = parser.parse_args()
    # --volume parameter
    vol = param.volume.strip()

    v = SysVolume()
    print(f"Volume is now {v.system_volume(vol)}%")
