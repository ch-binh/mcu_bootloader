import os

from utils.measure import measure_exe_time


class FileInfo:
    files = []
    fpath = ""
    origin_dir = "../../Release"

    @classmethod
    def scan_files(cls,
                   get_hexf: bool = False,
                   get_binf: bool = False,
                   get_elf: bool = False):
        """Scans for .hex, .bin, .elf files in the specified directory."""

        print("=" * 40)
        print("2. Listing all available bin or hex files")
        print("-" * 40 + "\n")
        if not os.path.exists(cls.origin_dir):
            print(f"Error: Directory '{cls.origin_dir}' does not exist.")
            return None

        cls.files = [
            f for f in os.listdir(cls.origin_dir)
            if (get_hexf and f.endswith(".hex")) or (
                get_binf and f.endswith(".bin")) or (
                    get_elf and f.endswith(".elf"))
        ]

        if not cls.files:
            print("No files found in", cls.origin_dir)
            return None

        print(f"Found {len(cls.files)} files in \"{cls.origin_dir}\":")
        for idx, file in enumerate(cls.files, start=0):
            print(f"{idx}. {file}")

    @classmethod
    def select_files(cls):
        print("--- Select file ---")
        print("Instruction: type \"1\" to select file no. 1")

        while True:
            try:
                idx = int(input("Input number: "))
                if 0 <= idx < len(cls.files):
                    break
                else:
                    print(
                        f"Invalid input, please enter a number between 0 and {len(cls.files) - 1}."
                    )
            except ValueError:
                print("Invalid input, please enter a valid number.")

        cls.fpath = os.path.abspath(f"{cls.origin_dir}/{cls.files[idx]}")

        print(f"\nSelect \"{cls.origin_dir}/{cls.files[idx]}\"\n")


class ImageInfo:

    def __init__(self,
                 flash_size=0x2000,
                 main_addr=0x0000,
                 cur_addr=0x0000,
                 s_addr=0xFFFFFFFF,
                 e_addr=0x00000000):
        self.flash_size = flash_size
        self.main_addr = main_addr
        self.cur_addr = cur_addr
        self.s_addr = s_addr
        self.e_addr = e_addr
        self.mem_buffer = [0xFF] * flash_size


#
# Conversion function
#============================================================================
@measure_exe_time
def dl_hexf_to_binf(fpath: str, ouputf_name: str = "app.bin") -> bool:
    from dl_hexf import dl_hexf_readf
    # Read hex file
    image = dl_hexf_readf(fpath)
    mem_buffer = image.mem_buffer
    image_size = image.e_addr - image.s_addr + 1

    # Write bin file
    save_fpath = os.path.abspath(f"../../Release/{ouputf_name}")
    try:
        with open(save_fpath, "wb") as f:
            f.write(bytearray(mem_buffer[:image_size]))

        print(
            f"Wrote {len(mem_buffer[:image_size])} bytes from 0x{image.s_addr:X} to 0x{image.e_addr :X} into {ouputf_name}"
        )
    except all:
        return False

    return True
