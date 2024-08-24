#!/usr/bin/env python3

import os
import tomllib

def get_conf(conf_file, keys):
    with open(conf_file, "rb") as fh: conf = tomllib.load(fh)
    return {k: conf[k] if k in conf else "" for k in keys}

class GalleryGenerator:
    def __init__(self, img_path, filetree, template, output_path):
        self.img_path = img_path
        self.filetree = filetree
        self.template = template
        self.output_path = output_path

    def generate_content(self):
        for year in sorted(self.filetree, reverse=True):
            for destination in sorted(self.filetree[year]):
                content = ""
                parameters = get_conf(f"{img_path}/{year}/{destination}/meta.toml", ["title"]) 

                content += self.heading(f"{year}_{destination}", parameters["title"])
                content += self.chapters(self.filetree[year][destination], f"{year}/{destination}")
                content += '<div class="images">'
                content += self.images([file for file in filetree[year][destination]["files"] if file.endswith((".jpg", ".jpeg", ".png"))], f"{year}/{destination}", f"{year}_{destination}")
                content += "</div>"


                content += '</div>\n</div>\n<br><hr>\n\n'
                self.out(self.output_path, f"{year}_{destination}.html", "{content}", content)

    def heading(self, html_class, title):
        return f'<div id="{html_class}">\n<h2>{title}</h2>\n<div>\n'

    def images(self, images, path: str, html_class: str):
        if images == []: return ""

        images_content = ""
        for images in sorted(images):
            img_path = f"{self.img_path}{path}/{images}"
            img_title = images.split(".")[0].split("_")[1]
            images_content += f'<a href="{img_path}" data-lightbox="{html_class}" data-title="{img_title}" data-alt="{img_title}"><img src="{img_path}" loading="lazy"></a>\n'
        return images_content

    def chapters(self, chapters, path: str):
        chapter_content = ""
        for chapter in sorted(chapters):
            if "files" not in chapter:
                parameters = get_conf(f"{self.img_path}/{path}/{chapter}/meta.toml", ["title"])
                chapter_content += f'<div class="chapter">\n<h4>{parameters["title"]}</h4>\n<div class="images">\n' if parameters["title"] != "" else f'<div class="chapter">\n<div class="images">\n'
                chapter_content += self.images([file for file in chapters[chapter]["files"] if file.endswith(("jpg", "jpeg", "png"))], f"{path}/{chapter}", path.replace("/", "_"))
                chapter_content += '</div>\n</div>\n<br><center>---<center><br>\n\n'
        
        return chapter_content

    def out(self, output_path, output_name, replacement_expression, output):
        with open(self.template, "r") as fh: page = fh.read()
        with open(output_path + output_name, "w") as fh: fh.write(page.replace(replacement_expression, output))

def generate_links(img_path, filetree, template, output_path):
    links = ""

    for year in sorted(filetree, reverse=True):
        for destination in filetree[year]:
            links += '<div class="links">'
            path = img_path + year + "/" + destination + "/"
            with open(path + "/meta.toml", "rb") as fh: meta = tomllib.load(fh)
            links += f'<a href="{year}_{destination}.html">{meta['title']}</a>\n'
            links += '</div>'

    with open(template, "r") as fh: page = fh.read()
    with open(output_path + "index.html", "w") as fh: fh.write(page.replace("{links}", links))

def generate_filetree(img_path):
    tree = {}

    for entry in os.listdir(img_path):
        full_path = os.path.join(img_path, entry)
        if os.path.isdir(full_path): tree[entry] = generate_filetree(full_path)
        else: tree.setdefault('files', []).append(entry)
    return tree



if __name__ == "__main__":
    parameters = get_conf("conf/conf.toml", ["img_path", "template_links", "template_trip", "output_path"])

    img_path = parameters["img_path"]
    template_links = parameters["template_links"]
    template_trip = parameters["template_trip"]
    output_path = parameters["output_path"]

    filetree = generate_filetree(img_path)

    generate_links(img_path, filetree, template_links, output_path)
    content_generator = GalleryGenerator(img_path, filetree, template_trip, output_path)
    content_generator.generate_content()
