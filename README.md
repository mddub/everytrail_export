# everytrail_export

A Python script which scrapes EveryTrail trip pages for trip stories, photos, and GPS data. Intended for the export of one's own trips.

See [this blog post][blog-post] for the motivation behind this tool.

## Installation

Install using `pip`:

```
pip install everytrail_export
```

If this fails because of permissions, try `pip install everytrail_export --user`.

If this fails because pip is not installed, follow these instructions: https://pip.pypa.io/en/latest/installing.html

## Usage

Installing with pip makes an executable called `everytrail_export` available from the command line. Invoking the script with no arguments gives usage instructions:

```
everytrail_export
```

If this fails, make sure that your system `$PATH` includes the location where executable scripts from Python packages are installed. (For example, if you installed with the `--user` option on OSX, package scripts are installed to `~/Library/Python/2.7/bin`.)

### The --trailauth option

**Downloading GPX/KML data from EveryTrail requires being logged in.** This means you need to pass the login cookie from your web browser so that the script can act as a logged-in user.

First, log into EveryTrail on your browser, which will set a cookie indicating to EveryTrail you are logged in. Then find the value of the `TRAILAUTH` cookie, which will be a long string of letters and numbers that looks like like `bce2a5ef9d3fd800e84f438f7237fe40dec5f1bd94cf67075ad17540ce956eed`. Finding this cookie can be done in at least two ways:

1. Follow the instructions on this WikiHow page to view your browser's cookies: http://www.wikihow.com/View-Cookies

2. While on an EveryTrail page, open your browser's web developer console (usually under the Tools menu) and type `document.cookie`. Look for the `TRAILAUTH` value.

You can then pass the script that value using the `--trailauth` option.

### The --trips-page option

If you use the `--trips-page` option to provide the URL for your trip listing page, then that list will scraped for individual trips to download. That way, you don't have to pass the trips one at a time to the script.

**To find your trips page,** make sure you are logged into EveryTrail, then hover your mouse over "My EveryTrail" in the menu at the top of the page, until you see the dropdown menu appear. Click "My Trips" in the dropdown menu. Copy the URL in the address bar of your browser.

### Putting it all together

Running the script with the `--trailauth` and `--trips-page` options will find all the trips listed at that URL, and then download the trips one by one:

```
$ everytrail_export --trailauth d9b61ab30a10... \
    --trips-page http://www.everytrail.com/my_trips.php?user_id=154142
Scraping http://www.everytrail.com/my_trips.php?user_id=154142 for trip URLs...
Found links to 15 trips: 1550019 1673357 1693258 1733157 1741278 1820769 1924844 1924847 2022884 2053816 2108623 2301920 2348794 2671553 2991898
Trip 1/15:
Downloading http://www.everytrail.com/view_trip.php?trip_id=1550019
  El Corte de Madera Creek Trail - California, United States
  Saved trails/1550019-el-corte-de-madera-creek-trail/title.txt
  Saved trails/1550019-el-corte-de-madera-creek-trail/info.html
  Saved trails/1550019-el-corte-de-madera-creek-trail/stats.html
  Saving GPX and KML files...
  Downloading http://www.everytrail.com/downloadGPX.php?trip_id=1550019
  Saved trails/1550019-el-corte-de-madera-creek-trail/1550019.gpx
  Downloading http://www.everytrail.com/downloadKML.php?trip_id=1550019
  Saved trails/1550019-el-corte-de-madera-creek-trail/1550019.kmz
  Downloading photos page: http://www.everytrail.com/trip_pictures.php?trip_id=1550019&code=
  Photo 1/13:
    Downloading photo info page: http://www.everytrail.com/view_picture.php?trip_id=1550019&picture_id=4326030
    Finding full photo: http://www.everytrail.com/picture/vieworiginal?picture_id=4336030
    Downloading full photo: http://images.everytrail.com/pics/original/4336030-IMG_8018.jpg
    Saved "IMG_8018" to trails/1550019-el-corte-de-madera-creek-trail/images/4336030-IMG_8018.jpg
...
  Saved trails/1550019-el-corte-de-madera-creek-trail/photo_info.json
Trip 2/15:
...
```

If you have so many trips that they span multiple listing pages (your trips page has a "Next" link at the bottom), then you will need to run the script for each listing page.

### Downloading individual trips

An alternative way to call the script is to download only a specific trip or trips. In that case, you can specify them as arguments:

```
$ everytrail_export --trailauth d9b61ab30a10... \
    http://www.everytrail.com/view_trip.php?trip_id=2671553 \
    http://www.everytrail.com/view_trip.php?trip_id=2991898 \
    http://www.everytrail.com/view_trip.php?trip_id=2348794
```

### --skip-photos

If you have lots of photos but want to download only trip stories and GPS data, the `--skip-photos` option will make the download much faster.

## Contact

If you have any questions, or run into trouble running this script, please email me at mark@warkmilson.com.

[blog-post]:    http://warkmilson.com/2015/03/20/exporting-from-everytrail.html
