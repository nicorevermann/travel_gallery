#!/usr/bin/env python3

import os
import tomllib

def get_conf(conf_file: str, keys: list) -> dict:
    with open(conf_file, "rb") as fh: conf = tomllib.load(fh)
    return {k: conf[k] if k in conf else "" for k in keys}

class GalleryGenerator:
    def __init__(self, base_path, file_tree, output_template, output_path):
        self.base_path = base_path
        self.output_template = output_template
        self.output_path = output_path
        self.all_files = self.flatten_files(file_tree, (".jpg", ".jpeg", ".png", ".toml", ".gpx"))
        self.images = self.flatten_files(file_tree, (".jpg", ".jpeg", ".png"))
        self.gpx_data = self.flatten_files(file_tree, ".gpx")

    def flatten_files(self, file_tree, file_type, current_path="") -> dict[str, list]:
        files = {}
        for key, value in file_tree.items():
            if isinstance(value, dict):
                new_path = f"{current_path}/{key}" if current_path else key
                files.update(self.flatten_files(value, file_type, new_path))
            elif key == "files":
                filtered_files = [f for f in value if f.endswith(file_type)]
                if filtered_files: files[current_path] = filtered_files
        return files

    def generate_content(self):
        output = {}
        for title,content in sorted(self.all_files.items()):
            year_destination = str("/".join(title.split("/")[:2]))
            if not year_destination in output: output[year_destination] = []
            if year_destination == title: 
                meta = get_conf(f"{self.base_path}{title}/meta.toml", ["title"])
                output[year_destination].append(self.heading(year_destination.replace("/", "_"), meta["title"], 2))
                if title in self.gpx_data: output[year_destination].insert(0, self.map())
                if title in self.images: output[year_destination].append(self.gallery(year_destination.replace("/", "_") ,title))
                output[year_destination].append('</div>\n</div>\n<br><hr>\n\n')
            else: output[year_destination].append(self.chapter(year_destination.replace("/", "_"), title))

        for trip,content in sorted(output.items(), reverse=True):
            self.out(f"{trip.replace("/", "_")}.html", "".join(content)) 

    def heading(self, html_class: str, title: str, size: int) -> str:
        return f'<div id="{html_class}">\n<h{str(size)}>{title}</h{str(size)}>\n<div>\n'

    def gallery(self, html_class, key: str) -> str:
        output = ['<div class="images">']
        for image in sorted(self.images[key]):
            img_path = self.base_path + key + "/" + image
            img_title = image.split("_")[1].split(".")[0] if image.split("_")[1] else ""
            output.append(f'<a href="{img_path}" data-lightbox="{html_class}" data-title="{img_title}" data-alt="{img_title}"><img src="{img_path}" loading="lazy"></a>\n')
        return "".join(output) + "</div>\n</div>\n</div>\n"

    def map(self):
        pass

    def chapter(self, html_class: str, key: str) -> str:
        output = ["<div>"]
        meta = get_conf(f"{self.base_path}{key}/meta.toml", ["title"])
        if "title" in meta: output.append(self.heading("_".join(key.split("/")[:3]), meta["title"], 3))
        if key in self.images: output.append(self.gallery(html_class, key))
        return "".join(output) + "</div><br>"

    def out(self, output_name, output_html):
        with open(self.output_template, "r") as fh: page = fh.read()
        with open(self.output_path + output_name, "w") as fh: fh.write(page.replace("{content}", output_html))

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
