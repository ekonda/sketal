from PIL import Image, ImageDraw, ImageFont

def main():
    chars = ""
    for c in """qwertyuiop[]asdfghjkl;'zxcvbnm,./1234567890-='йцукенгшщзхъфывапролджэячсмитьбю.] """:
        if c not in chars:
            chars += c
            if c.upper() != c:
                chars += c.upper()
    chars = "".join(sorted(list(chars), reverse=True))

    m = {}

    size = (7, 9)
    for c in chars:
        im = Image.new("1", size)
        fn = ImageFont.truetype('5by7.regular.ttf', 10)
        dr = ImageDraw.Draw(im)

        dr.text((0, 1), c, font=fn, fill=(1,))

        obj = [""]
        for i in range(size[1]):
            for j in range(size[0]):
                obj[-1] += str(im.getpixel((j, i)))
            obj[-1] = "0" + obj[-1] + "0"
            obj.append("")

        m[c] = obj

    import json
    with open("data", "w") as o:
        json.dump(m, o)

if __name__ == "__main__":
    main()
