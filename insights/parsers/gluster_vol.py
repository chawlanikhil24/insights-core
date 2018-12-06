"""
Gluster vol info - command  to retrive information of gluster volumes
=====================================================================

The parsers here provide information about the time sources used by
``glusterd``.
"""
from insights.core.plugins import parser
from insights.core import CommandParser, LegacyItemAccess
from insights.parsers import ParseException, get_active_lines, parse_fixed_table
from insights.specs import Specs


@parser(Specs.gluster_v_info)
class GlusterVolInfo(LegacyItemAccess, CommandParser):
    """
    This parser processes the output of the command `gluster vol info` and provides
    the information as a dictionary.

    The LegacyItemAccess class provides some helper functions for dealing with a
    class having a `data` attribute.

    Sample input::

        Volume Name: test_vol
        Type: Replicate
        Volume ID: 2c32ed8d-5a07-4a76-a73a-123859556974
        Status: Started
        Snapshot Count: 0
        Number of Bricks: 1 x 3 = 3
        Transport-type: tcp
        Bricks:
        Brick1: 172.17.18.42:/home/brick
        Brick2: 172.17.18.43:/home/brick
        Brick3: 172.17.18.44:/home/brick

    Examples:

        >>> vol_info.data['test_vol']['Type']
        'Replicate'
    """

    def parse_content(self, content):
        """
        Override the base class parse_content to parse the output of the '''gluster vol info'''  command.
        Information that is stored in the object is made available to the rule plugins.

        Attributes:
            data (dict): Dictionary containing each of the key:value pairs from the command
                output.

        Raises:
            ParseException: raised if data is not parsable."""

        # Stored data in a dictionary data structure
        self.data = {}

        name = None
        body = {}

        # Input data is available in text file. Reading each line in file and parsing it to a dictionary.
        for line in get_active_lines(content):
            if ':' in line:
                key, val = line.strip().split(":", 1)
                key = key.strip()
                val = val.lstrip()
            else:
                raise ParseException("Unable to parse gluster volume options: {}".format(content))
            if key == "Volume Name":
                if name is None:
                    name = val
                else:
                    self.data[name] = body
                    name = val
                    body = {}
            else:
                body[key.strip()] = val.lstrip(" ")

        if name and body:
            self.data[name] = body

        if not self.data:
            # If no data is obtained in the command execution then throw an exception instead of returning an empty
            # object.  Rules depending solely on this parser will not be invoked, so they don't have to
            # explicitly check for invalid data.
            raise ParseException("Unable to parse gluster volume options: {0}".format(content))


@parser(Specs.gluster_v_status)
class GlusterVolStatus(LegacyItemAccess, CommandParser):
    """
    This parser processes the output of the command `gluster vol status` and provides
    the information as a dictionary.

    The LegacyItemAccess class provides some helper functions for dealing with a
    class having a `data` attribute.

    Sample input::

        Status of volume: test_vol
        Gluster process                             TCP Port  RDMA Port  Online  Pid
        ------------------------------------------------------------------------------
        Brick 172.17.18.42:/home/brick              49152     0          Y       26685
        Brick 172.17.18.43:/home/brick              49152     0          Y       27094
        Brick 172.17.18.44:/home/brick              49152     0          Y       27060
        Self-heal Daemon on localhost               N/A       N/A        Y       7805
        Self-heal Daemon on 172.17.18.44            N/A       N/A        Y       33400
        Self-heal Daemon on 172.17.18.43            N/A       N/A        Y       33680

        Task Status of Volume test_vol
        ------------------------------------------------------------------------------
        There are no active volume tasks


    Examples:

        >>> parser_result.data["test_vol"][0]
        {'Gluster_process': 'Brick 172.17.18.42:/home/brick', 'RDMA Port': '0', 'IP': '172.17.18.42', 'TCP Port': '49152', 'Pid': '26685', 'Online': 'Y', 'Directory': '/home/brick'}

    """

    def parse_content(self, content):
        """
        Override the base class parse_content to parse the output of the '''gluster vol status'''  command.
        Information that is stored in the object is made available to the rule plugins.

        Attributes:
            data (dict): Dictionary containing each of the key:value pairs from the command
                output.

        Raises:
            ParseException: raised if data is not parsable."""

        # Stored data in a dictionary data structure
        self.data = {}
        content = get_active_lines(content, '----')
        idxs = [i for i, l in enumerate(content) if l.startswith('Status of volume')]
        for i, idx in enumerate(idxs):
            start = idx
            end = idxs[i+1] if i < len(idxs) - 1 else -1
            _, val = content[idx].split(":", 1)
            body = parse_fixed_table(
                    content[start:end],
                    header_substitute=[('Gluster process', 'Gluster_process'),
                                       ('TCP Port', 'TCP_Port'),
                                       ('RDMA Port', 'RDMA_Port'),
                                      ],
                    heading_ignore=['Gluster process'],
                    trailing_ignore=['Task Status'])
            for v in body:
                gluster_process = v['Gluster_process']
                if gluster_process.startswith("Brick"):
                    _ip, _dir = gluster_process.split(':', 1)
                    v['IP'] = _ip.split()[-1].strip()
                    v['Directory'] = _dir.strip()
                elif gluster_process.startswith("Self-heal"):
                    v['Host'] = gluster_process.split()[-1]
            self.data[val.strip()] = body
        if not self.data:
            # If no data is obtained in the command execution then throw an exception instead of returning an empty
            # object.  Rules depending solely on this parser will not be invoked, so they don't have to
            # explicitly check for invalid data.
            raise ParseException("Unable to parse gluster volume status: {0}".format(content))
