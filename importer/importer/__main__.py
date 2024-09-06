import argparse
from kmstr_base import Kmstr

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Monitor your vehicles with kmstr"
    )
    parser.add_argument('-u', '--username', required=True, type=str, help="Username to log in We Connect")
    parser.add_argument('-p', '--password', required=True, type=str, help="Password to log in We Connect")
    parser.add_argument('-i', '--interval', required=False, type=int, default=180, help='Query interval in seconds')
    parser.add_argument('--db-hostname', required=False, type=str, default='db', help='Database hostname (default: db)')
    parser.add_argument('--db-username', required=False, type=str, default='kmstr_appl', help='Database username (default: kmstr_appl)')
    parser.add_argument('--db-password', required=False, type=str, default='secure', help='Database password (default: secure)')
    parser.add_argument('--db-name', required=False, type=str, default='kmstr', help='Database name (default: kmstr)')
    parser.add_argument('--db-port', required=False, type=int, default='5432', help='Database port (default: 5432)')
    parser.add_argument('-tz', '--timezone', required=False, type=str, default='Europe/Zurich', help='Timezone (default: Europe/Zurich)')

    args = parser.parse_args()

    kmstr = Kmstr(
        username=args.username,
        password=args.password,
        interval=args.interval,
        db_hostname=args.db_hostname,
        db_username=args.db_username,
        db_password=args.db_password,
        db_name=args.db_name,
        db_port=args.db_port,
        tz=args.timezone
    )
    kmstr.run()
