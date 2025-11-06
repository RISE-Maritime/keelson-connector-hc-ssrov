import argparse


def terminal_inputs():
    """Parse the terminal inputs and return the arguments"""

    parser = argparse.ArgumentParser(
        prog="keelson_connector_hc_ssrov",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Read ROV Hand Controller from joystick device and publish to Keelson/Zenoh",
    )

    parser.add_argument(
        "-l",
        "--log-level",
        type=int,
        default=20,
        help="Log level 10=DEBUG, 20=INFO, 30=WARN, 40=ERROR, 50=CRITICAL 0=NOTSET",
    )

    parser.add_argument(
        "--mode",
        "-m",
        dest="mode",
        choices=["peer", "client"],
        type=str,
        help="The zenoh session mode.",
    )

    parser.add_argument(
        "--connect",
        action="append",
        type=str,
        help="Endpoints to connect to, in case multicast is not working. ex. tcp/localhost:7447",
    )

    parser.add_argument(
        "-r",
        "--realm",
        default="rise",
        type=str,
        help="Unique id for a domain/realm to connect ex. rise",
    )

    parser.add_argument(
        "-e",
        "--entity-id",
        default="rov",
        type=str,
        help="Entity being a unique id representing an entity within the realm",
    )

    parser.add_argument(
        "-s",
        "--source-id",
        default="controller/hc",
        type=str,
        help="Source id being a unique id representing the source of the data",
    )

    parser.add_argument(
        "--device",
        "-d",
        type=str,
        default="/dev/input/js0",
        help="Joystick device path (default: /dev/input/js0)",
    )

    # Parse arguments and start doing our thing
    args = parser.parse_args()

    return args
