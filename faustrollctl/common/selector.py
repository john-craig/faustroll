import logging

from faustrollctl.common.constants import RC_OK, RC_BAD
from faustrollctl.common.utils import run_command

logger = logging.getLogger(__name__)

class Selector:
    @staticmethod
    def select_from_list(lst, small=False):
        cmd = ["/usr/bin/rofi", "-p", ">>>", "-dmenu"]

        if small:
            cmd = cmd + ["-font", "\"Monospace 12\""]

        stdin_str = "\n".join(lst)
        rc, stdout = run_command(cmd, input=stdin_str)

        if rc != RC_OK:
            logger.warning(f"Error with selecting from list, return code: {rc}")
            return (rc, None)

        sel = stdout.strip("\n")

        return (RC_OK, sel)

    @staticmethod
    def enter_text(small=False):
        # This hack has three parts:
        #  -kb-accept-custom is set to 'Return' key so that it accepts whatever string the user
        #  has written
        #  -kb-accept-entry  is set to 'Ctrl+Return' so that the 'Return' key is free for use
        #  -l overrides the number of lines to 0, which makes the text box look like just an input
        #   field and basically nothing else
        cmd = ["/usr/bin/rofi", 
            "-p", ">>>",
            "-dmenu",
            "-kb-accept-custom", "Return", 
            "-kb-accept-entry", "Ctrl+Return",
            "-l", "0"
        ]

        if small:
            cmd = cmd + ["-font", "\"Monospace 12\""]

        rc, stdout = run_command(cmd, input="")

        if rc != RC_OK:
            return (rc, None)

        text = stdout.strip('\n')

        return (rc, text)