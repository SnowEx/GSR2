# Cheat Sheet adding missing Exif tags
An initial iteration to download images from the Sony camera had some missing
essential exif image tags. The first solution was to manually add them, but
changing the download software to [digiKam](https://www.digikam.org/) preserved
the information.

## 'exiv2' command line tool
Site: https://exiv2.org/
Code: https://github.com/exiv2/exiv2

### Commands
#### Camera Make#
```shell
exiv2 --Modify "add Exif.Image.Make SONY" image.jpg
```

#### Camera Model
```shell
exiv2 --Modify "add Exif.Image.Model ILCE-6000" image.jpg
```

#### Focal length
```shell
exiv2 --Modify "add Exif.Photo.FocalLength 24/1" image.jpg
```

#### ISO value
```shell
exiv2 --Modify "add Exif.Photo.ISOSpeedRatings 200" image.jpg
```

### Links
Possible tags: https://exiv2.org/tags.html
