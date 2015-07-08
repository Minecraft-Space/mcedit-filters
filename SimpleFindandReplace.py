# A simple find and replace filter for mcedit
# If there are any issues or enhancement requests please submit a bug report at:
# https://github.com/qqii/mcedit-filters
import re
from pymclevel import TAG_String
from pymclevel import TAG_List
from pymclevel import TAG_Compound

displayName = "Simple Find and Replace"

inputs = (
    ("Formatting Character", ("string", "value=%%")),
    ("The formatting character is replaced by " + unichr(167) + ".", "label"),
    ("Blacklist", ("string", "value=id;")),
    ("A blacklist of names sepereated by \";\" which are not replaced.", "label"),
    ("Regex Mode", False),
    ("Enable finding via a python regular expression. Optionally end the regex with \"&&\" followed by the re.<LETTER> (e.g. <regex>&&M to enable multi line pattern searching).", "label"),
    ("Find", ("string","value=")),
    ("Replace", ("string","value=")),
)


# A blacklist of names for NBT tags that are not replaced
# By default this contains "id" as editing the id of mobs may cause unwanted effects
blacklist = []
compiledExpr = None

# The following functions finds and replaces text in string tags recursively
# Each of them all returns true if text was replaced
# A call should be made to replace_TAG_Compound with the entity or tile entity NBT compound tag
def replace_TAG_String(tagString, find, replace):
    # This prevents people from trying to find and replace quotes in their text 
    # adding stuff to the start and end of their strings
    old = tagString.value.strip('"')
    if compiledExpr is None:
        tagString.value = old.replace(find, replace)
    else:
        tagString.value = compiledExpr.sub(replace, old)
    return not tagString.value == old

def replace_TAG_List(tagList, find, replace):
    replaced = False

    for tag in tagList:
        if replace_TAG(tag, find, replace):
            replaced = True

    return replaced

def replace_TAG_Compound(tagCompound, find, replace):
    replaced = False

    for name, tag in tagCompound.iteritems():
        if name not in blacklist:
            if replace_TAG(tag, find, replace):
                replaced = True

    return replaced

def replace_TAG(tag, find, replace):
    replaced = False
    tagType = type(tag)

    if tagType == TAG_String:
        if replace_TAG_String(tag, find, replace):
            replaced = True
    elif tagType == TAG_List:
        if replace_TAG_List(tag, find, replace):
            replaced = True
    elif tagType == TAG_Compound:
        if replace_TAG_Compound(tag, find, replace):
            replaced = True

    return replaced

def perform(level, box, options):
    global blacklist
    global compiledExpr

    formatChr = options["Formatting Character"]
    blacklist = options["Blacklist"].split(";")

    # unichr(167) is the formatting character for minecraft
    find = options["Find"].replace(formatChr, unichr(167))
    replace = options["Replace"].replace(formatChr, unichr(167))

    if options["Regex Mode"]:
        regex = find
        flags = 0
        if "&&" in find:
            print find
            regex, strFlags = find.split("&&")
            # TODO?: Replace this with dynamic code, something like this
            # for letter in (l for l in dir(re) if len(l) == 1):
            #   flags |= re.__dict__[letter]
            if "A" in strFlags:
                flags |= re.A
            if "I" in strFlags:
                flags |= re.I
            if "L" in strFlags:
                flags |= re.L
            if "M" in strFlags:
                flags |= re.M
            if "S" in strFlags:
                flags |= re.S
            if "U" in strFlags:
                flags |= re.U
            if "X" in strFlags:
                flags |= re.X
            print strFlags, flags
        print
        print regex, flags
        compiledExpr = re.compile(regex, flags)
    else:
        compiledExpr = None

    for chunk, slices, point in level.getChunkSlices(box):
        for compoundTag in chunk.getEntitiesInBox(box) + chunk.getTileEntitiesInBox(box):
            print compoundTag
            if replace_TAG(compoundTag, find, replace):
                chunk.dirty = True
