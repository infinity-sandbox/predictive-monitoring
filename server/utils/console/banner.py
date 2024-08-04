from utils.console.io import IO


_MAIN_BANNER = r"""{}

    _                _ _                         _    ___ 
   / \   _ __  _ __ | (_) ___ __ _ _ __ ___     / \  |_ _|
  / _ \ | '_ \| '_ \| | |/ __/ _` | '__/ _ \   / _ \  | | 
 / ___ \| |_) | |_) | | | (_| (_| | | |  __/  / ___ \ | | 
/_/   \_\ .__/| .__/|_|_|\___\__,_|_|  \___| /_/   \_\___|
        |_|   |_|                                         

""".format(IO.Fore.LIGHTRED_EX, IO.Style.RESET_ALL + IO.Style.BRIGHT)                                    

def get_main_banner(banner=_MAIN_BANNER):
    return banner

def run_banner():
    """
    Main entry point of the application
    @fetch version from a function
    """

    IO.spacer()
    IO.print(get_main_banner(_MAIN_BANNER))
    IO.spacer()
