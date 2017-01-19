Commands
========

::

    usage: landsat [-h] [--version] {search,download,process} ...

    Landsat-util is a command line utility that makes it easy to
    search, download, and process Landsat imagery.

        Commands:
            Search:
                landsat.py search [-p --pathrow] [--lat] [--lon] [-l LIMIT] [-s START] [-e END] [-c CLOUD] [-h]

                optional arguments:
                    -p, --pathrow       Paths and Rows in order separated by comma. Use quotes "001,003".
                                        Example: path,row,path,row 001,001,190,204

                    --lat               Latitude

                    --lon               Longitude

                    --address           Street address

                    -l LIMIT, --limit LIMIT
                                        Search return results limit default is 10

                    -s START, --start START
                                        Start Date - Most formats are accepted e.g.
                                        Jun 12 2014 OR 06/12/2014

                    -e END, --end END   End Date - Most formats are accepted e.g.
                                        Jun 12 2014 OR 06/12/2014

                    --latest N          Returns the N latest images within the last 365 days.

                    -c CLOUD, --cloud CLOUD
                                        Maximum cloud percentage. Default: 20 perct

                    --json              Returns a bare JSON response

                    --geojson             Returns a geojson response

                    -h, --help          Show this help message and exit

            Download:
                landsat download sceneID [sceneID ...] [-h] [-b --bands]

                positional arguments:
                    sceneID     Provide Full sceneIDs. You can add as many sceneIDs as you wish

                    Example: landast download LC81660392014196LGN00

                optional arguments:
                    -b --bands          If you specify bands, landsat-util will try to download the band from S3.
                                        If the band does not exist, an error is returned

                    -h, --help          Show this help message and exit

                    -d, --dest          Destination path

                    -p, --process       Process the image after download

                    --pansharpen        Whether to also pansharpen the processed image.
                                        Pansharpening requires larger memory

                    --ndvi              Calculates NDVI and produce a RGB GTiff with separate colorbar.

                    --ndvigrey          Calculates NDVI and produce a greyscale GTiff.

                    --clip              Clip the image with the bounding box provided. Values must be in WGS84 datum,
                                        and with longitude and latitude units of decimal degrees separated by comma.
                                        Example: --clip=-346.06658935546875,49.93531194616915,-345.4595947265625,50.2682767372753

                    -u --upload         Upload to S3 after the image processing completed

                    --key               Amazon S3 Access Key (You can also be set AWS_ACCESS_KEY_ID as
                                        Environment Variables)

                    --secret            Amazon S3 Secret Key (You can also be set AWS_SECRET_ACCESS_KEY as
                                        Environment Variables)

                    --bucket            Bucket name (required if uploading to s3)

                    --region            URL to S3 region e.g. s3-us-west-2.amazonaws.com

                    --force-unzip       Force unzip tar file

            Process:
                landsat.py process path [-h] [-b --bands] [-p --pansharpen]

                positional arguments:
                    path          Path to the landsat image folder or zip file

                optional arguments:
                    -b --bands             Specify bands. The bands should be written in sequence with no spaces
                                        Default: Natural colors (432)
                                        Example --bands 432

                    --pansharpen        Whether to also pansharpen the process image.
                                        Pansharpening requires larger memory

                    --ndvi              Calculates NDVI and produce a RGB GTiff with separate colorbar.

                    --ndvigrey          Calculates NDVI and produce a greyscale GTiff.

                    --clip              Clip the image with the bounding box provided. Values must be in WGS84 datum,
                                        and with longitude and latitude units of decimal degrees separated by comma.
                                        Example: --clip=-346.06658935546875,49.93531194616915,-345.4595947265625,50.2682767372753

                    -v, --verbose       Show verbose output

                    -h, --help          Show this help message and exit

                    -u --upload         Upload to S3 after the image processing completed

                    --key               Amazon S3 Access Key (You can also be set AWS_ACCESS_KEY_ID as
                                        Environment Variables)

                    --secret            Amazon S3 Secret Key (You can also be set AWS_SECRET_ACCESS_KEY as
                                        Environment Variables)

                    --bucket            Bucket name (required if uploading to s3)

                    --region            URL to S3 region e.g. s3-us-west-2.amazonaws.com

                    --force-unzip       Force unzip tar file

    positional arguments:
      {search,download,process}
                            Landsat Utility
        search              Search Landsat metadata
        download            Download images from Google Storage
        process             Process Landsat imagery

    optional arguments:
      -h, --help            show this help message and exit
      --version             show program's version number and exit
