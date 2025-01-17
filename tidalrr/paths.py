#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :  paths.py
@Date    :  2022/06/10
@Author  :  Yaronzz
@Version :  1.0
@Contact :  yaronhuang@foxmail.com
@Desc    :  
"""

import aigpy
import datetime
from tidalrr.model import StreamUrl, Album, Type, AudioQuality
from tidalrr.database import getSettings
from tidalrr.database.artists import getTidalArtist

def fixPath(name: str):
    return aigpy.path.replaceLimitChar(name, '-').strip()


def getYear(releaseDate: str):
    if releaseDate is None or releaseDate == '':
        return ''
    return aigpy.string.getSubOnlyEnd(releaseDate, '-')


def getDurationStr(seconds):
    time_string = str(datetime.timedelta(seconds=seconds))
    if time_string.startswith('0:'):
        time_string = time_string[2:]
    return time_string


def __getExtension__(stream: StreamUrl):
    if '.flac' in stream.url:
        return '.flac'
    if '.mp4' in stream.url:
        if 'ac4' in stream.codec or 'mha1' in stream.codec:
            return '.mp4'
        elif 'flac' in stream.codec:
            if 'DASH' in stream.codec:
                return '.mp4'
            return '.flac'
        return '.m4a'
    return '.m4a'

def getFlag(data, type: Type, short=True, separator=" / "):
        master = False
        atmos = False
        explicit = False
        if type == Type.Album or type == Type.Track:
            if data.audioQuality == "HI_RES":
                master = True
            if type == Type.Album and "DOLBY_ATMOS" in data.audioModes:
                atmos = True
            if data.explicit is True:
                explicit = True
        if not master and not atmos and not explicit:
            return ""
        array = []
        if master:
            array.append("M" if short else "Master")
        if atmos:
            array.append("A" if short else "Dolby Atmos")
        if explicit:
            array.append("E" if short else "Explicit")
        return separator.join(array)

def getAlbumPath(album:Album):
    settings = getSettings()
    artist = getTidalArtist(album.artist)
    if artist is not None:
        artists = album.artists.split(", ")[:1]
        artists = ", ".join(artists)[:50]
        artistName = fixPath(str(artists))
        albumArtistName = fixPath(artist.name) if album.artist is not None else ""
        # album folder pre: [ME]
        flag = getFlag(album, Type.Album, True, "")
        if settings.audioQuality != AudioQuality.Master and settings.audioQuality != AudioQuality.Max:
            flag = flag.replace("M", "")
        if flag != "":
            flag = "[" + flag + "] "

        # album and addyear
        albumName = fixPath(album.title)
        year = getYear(album.releaseDate)

        # retpath
        retpath = settings.albumFolderFormat
        if retpath is None or len(retpath) <= 0:
            retpath = settings.getDefaultAlbumFolderFormat()
        retpath = retpath.replace(R"{ArtistName}", artistName)
        retpath = retpath.replace(R"{AlbumArtistName}", albumArtistName)
        retpath = retpath.replace(R"{Flag}", flag)
        retpath = retpath.replace(R"{AlbumID}", str(album.id))
        retpath = retpath.replace(R"{AlbumYear}", year)
        retpath = retpath.replace(R"{AlbumTitle}", albumName)
        retpath = retpath.replace(R"{AudioQuality}", album.audioQuality)
        retpath = retpath.replace(R"{DurationSeconds}", str(album.duration))
        retpath = retpath.replace(R"{Duration}", getDurationStr(album.duration))
        retpath = retpath.replace(R"{NumberOfTracks}", str(album.numberOfTracks))
        retpath = retpath.replace(R"{NumberOfVolumes}", str(album.numberOfVolumes))
        retpath = retpath.replace(R"{ReleaseDate}", str(album.releaseDate))
        retpath = retpath.replace(R"{RecordType}", album.type)
        retpath = retpath.replace(R"{None}", "")
        retpath = retpath.strip()
        return f"{settings.downloadPath}/{retpath}"

def getPlaylistPath(playlist):
    playlistName = fixPath(playlist.title)
    settings = getSettings()
    # retpath
    retpath = settings.playlistFolderFormat
    if retpath is None or len(retpath) <= 0:
        retpath = settings.getDefaultPlaylistFolderFormat()
    retpath = retpath.replace(R"{PlaylistUUID}", str(playlist.uuid))
    retpath = retpath.replace(R"{PlaylistName}", playlistName)
    return f"{settings.downloadPath}/{retpath}"


def getTrackPath(track, stream, artist=None, album=None, playlist=None, filename=None):
    settings = getSettings()
    base = './'
    number = str(track.trackNumber).rjust(2, '0')
    if album.numberOfVolumes > 1:
        # Prepend the disc number to the track number
        # For disc 2 track 01, this becomes '201'
        number = str(track.volumeNumber) + str(track.trackNumber).rjust(2, '0')
    if album is not None:
        base = getAlbumPath(album)

    if playlist is not None and settings.usePlaylistFolder:
        base = getPlaylistPath(playlist)
        number = str(track.trackNumberOnPlaylist).rjust(2, '0')
    # artist
    artists = ""
    if track.artists is not None:
        # only save the first 5 artists in the folder name
        artists = track.artists.split(", ")[:1]
        artists = ", ".join(artists)[:50]
        artists = fixPath(str(track.artists)) 

    artist = getTidalArtist(track.artist)
    if artist is not None:
        artist = fixPath(artist.name[:50])

    # title
    title = fixPath(track.title)[:150]
    if not aigpy.string.isNull(track.version):
        title += f' ({fixPath(track.version)})'

    # explicit
    explicit = "(Explicit)" if track.explicit else ''

    # album and addyear
    albumName = fixPath(album.title) if album is not None else ''
    year = getYear(album.releaseDate) if album is not None else ''

    # extension
    extension = __getExtension__(stream)

    retpath = settings.trackFileFormat
    if retpath is None or len(retpath) <= 0:
        retpath = settings.getDefaultTrackFileFormat()
    retpath = retpath.replace(R"{TrackNumber}", number)
    retpath = retpath.replace(R"{ArtistName}", artist)
    retpath = retpath.replace(R"{ArtistsName}", artists)
    retpath = retpath.replace(R"{TrackTitle}", title)
    retpath = retpath.replace(R"{ExplicitFlag}", explicit)
    retpath = retpath.replace(R"{AlbumYear}", year)
    retpath = retpath.replace(R"{AlbumTitle}", albumName)
    retpath = retpath.replace(R"{AudioQuality}", track.audioQuality)
    retpath = retpath.replace(R"{DurationSeconds}", str(track.duration))
    retpath = retpath.replace(R"{Duration}", getDurationStr(track.duration))
    retpath = retpath.replace(R"{TrackID}", str(track.id))
    retpath = retpath.strip()
    if filename is not None:
        return f"{retpath}{extension}"
    else:
        return f"{base}/{retpath}{extension}"
