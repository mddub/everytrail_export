from scraper import get_trip_ids_from_listing_page, download_trip, _normalize_arg_to_id

USAGE = '%prog trip_id_or_url_1 [trip_id_or_url_2 ...] [--trailauth COOKIE] [options]'
DESCRIPTION = "Scrape EveryTrail trip page(s) and download their contents, including GPX, story, and photos. Arguments may be EveryTrail trip IDs (e.g. 2991898) or trip page URLs (e.g. http://everytrail.com/view_trip.php?trip_id=2991898)."
OUT_DIR = 'trails'

def main():
    import os
    import sys
    from optparse import OptionParser

    parser = OptionParser(usage=USAGE, description=DESCRIPTION)
    parser.add_option('--trailauth',
        action='store', type='string', dest='trailauth', metavar='COOKIE',
        help='the value of the TRAILAUTH cookie from your web browser where you are logged into EveryTrail. This is necessary to enable downloading GPX/KML files. It looks something like "d9b61a...". (See README for help on finding this value.)')
    parser.add_option('--trips-page',
        action='store', type='string', dest='trips_page', metavar='URL',
        help='the URL of a trip listing page which will be scraped for individual trip URLs, e.g. http://everytrail.com/my_trips.php?user_id=154142. This can be used instead of, or in addition to, specifying trip IDs/URLs as command arguments.')
    parser.add_option('--skip-photos',
        action='store_true', dest='skip_photos', default=False,
        help="don't download photos")
    parser.add_option('--out-dir',
        action='store', type='string', dest='out_dir', default=OUT_DIR,
        help="optionally specify output directory where trip data will be saved (default: %default)")

    options, args = parser.parse_args(sys.argv[1:])

    trip_ids = map(_normalize_arg_to_id, args)
    if options.trips_page:
        trip_ids += get_trip_ids_from_listing_page(options.trips_page)

    if not trip_ids and not options.trips_page:
        parser.print_help()
        sys.exit(0)

    if not options.trailauth:
        print "Will not download GPX/KML files since no TRAILAUTH cookie was provided. `python {0} --help` for more information.".format(os.path.basename(sys.argv[0]))

    for i, trip_id in enumerate(trip_ids):
        print "Trip {0}/{1}:".format(i + 1, len(trip_ids))
        download_trip(trip_id, options.out_dir, trailauth_cookie=options.trailauth, skip_photos=options.skip_photos)
