from jplephem.spk import SPK


def load_bsp(file_path: str) -> SPK:
    """加载 BSP 文件，返回 SPK 对象"""
    return SPK.open(file_path)
