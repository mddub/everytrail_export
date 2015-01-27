import os
import re
import time

import requests
import simplejson as json
from pyquery import PyQuery as pq

URL_BASE = 'http://www.everytrail.com'
OUT_DIR = 'trails'

# TODO: could get this from a user's trip listing page
my_trips = [
    "/view_trip.php?trip_id=1550019",
    "/view_trip.php?trip_id=1673357",
    "/view_trip.php?trip_id=1693258",
    "/view_trip.php?trip_id=1733157",
    "/view_trip.php?trip_id=1741278",
    "/view_trip.php?trip_id=1820769",
    "/view_trip.php?trip_id=1924844",
    "/view_trip.php?trip_id=1924847",
    "/view_trip.php?trip_id=2022884",
    "/view_trip.php?trip_id=2053816",
    "/view_trip.php?trip_id=2108623",
    "/view_trip.php?trip_id=2301920",
    "/view_trip.php?trip_id=2348794",
    "/view_trip.php?trip_id=2671553",
    "/view_trip.php?trip_id=2991898",
]

trip_ids_and_urls = [
    (trip_path.split('=')[-1], URL_BASE + trip_path)
    for trip_path
    in sorted(my_trips)
]

for trip_id, trip_url in trip_ids_and_urls:
    print trip_url
    trip_page = pq(requests.get(trip_url).content)

    title = trip_page.find('h1 span').text()
    location = re.sub('^ -', '', trip_page.find('h1').remove('span').text())

    # Output dir == something like 'trails/1820769-mt-tam-ridgecrest-blvd-to-al'
    title_for_dir = re.sub('[:/\ ]', '-', title.lower()[:30])
    title_for_dir = title_for_dir.replace('.', '')
    title_for_dir = re.sub('--+', '-', title_for_dir)

    trip_dir = os.path.join(OUT_DIR, '-'.join([trip_id, title_for_dir]))
    try:
        os.makedirs(os.path.join(trip_dir, 'images'))
    except OSError:
        pass

    print "  Saving trip info: {0}".format(title)
    with open(os.path.join(trip_dir, 'title'), 'w') as f:
        f.write('\n'.join([title, location]))

    info_html = trip_page.find('.main-column-container.left div div').html()
    with open(os.path.join(trip_dir, 'info.html'), 'w') as f:
        f.write(info_html.encode('utf-8'))

    stats_html = trip_page.find('.right-column.left .content').filter(
        lambda _, e: 'Trip Info' in pq(e).text()
    ).html()
    with open(os.path.join(trip_dir, 'stats.html'), 'w') as f:
        f.write(stats_html.encode('utf-8'))

    time.sleep(1)

    photos_link = trip_page.find('a').filter(lambda _, a: 'See all pictures' in pq(a).text())
    if photos_link:
        print "  Downloading photos..."

        photos_page = pq(requests.get(URL_BASE + photos_link.eq(0).attr('href')).content)
        photo_urls = [
            URL_BASE + e.attrib['href']
            for e
            in photos_page.find('.pictures-container .center a')
        ]

        photo_info = []
        for photo_url in photo_urls:
            photo_page = pq(requests.get(photo_url).content)
            lat_lng = re.search('GLatLng\(([^)]+)\)', photo_page.html()).group(1)
            lat, lng = map(float, lat_lng.split(', '))
            photo_title = photo_page.find('h2.big-title').text()

            original_image_page_url = photo_page.find('a').filter(
                lambda _, a: 'View Original' in pq(a).text()
            ).attr('href')

            original_image_page = pq(requests.get(URL_BASE + original_image_page_url).content)
            image_url = original_image_page.find('img').attr('src')
            image_filename = image_url.split('/')[-1]
            with open(os.path.join(trip_dir, 'images', image_filename), 'wb') as f:
                for chunk in requests.get(image_url, stream=True):
                    f.write(chunk)

            photo_info.append({
                'lat': lat,
                'lng': lng,
                'title': photo_title,
                'filename': image_filename,
            })

            print '    {0} ("{1}")'.format(image_filename, photo_title)
            time.sleep(1)

        with open(os.path.join(trip_dir, 'photo_info.json'), 'w') as f:
            f.write(json.dumps(photo_info, indent=4 * ' '))
