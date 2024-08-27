#!/usr/bin/env python3

import os
import tomllib
import hashlib
from PIL import Image
from concurrent.futures import ProcessPoolExecutor

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
                output[year_destination].append('</div>\n</div>\n<br>\n\n')
            else: output[year_destination].append(self.chapter(year_destination.replace("/", "_"), title))

        for trip,content in sorted(output.items(), reverse=True):
            self.out(f"{trip.replace("/", "_")}.html", "".join(content)) 

    def heading(self, html_class: str, title: str, size: int) -> str:
        return f'<div id="{html_class}">\n<h{str(size)}>{title}</h{str(size)}>\n<div>\n'

    def gallery(self, html_class, key: str) -> str:
        output = ['<div class="images">\n']
        futures = []
        images_out_path = f"{self.output_path}out_img/"
        thumbnail_out_path = f"{self.output_path}out_img/tn/"
        for path in (images_out_path, thumbnail_out_path): os.makedirs(path, exist_ok=True)

        with ProcessPoolExecutor() as executor:
            for image in sorted(self.images[key]):
                img_path = self.base_path + key + "/" + image
                thumbnail_path = self.base_path + key + "/" + image

                future_img = executor.submit(self.shrink_and_compress_image, img_path, "webp", images_out_path, (2304, 2304))
                future_thumb = executor.submit(self.shrink_and_compress_image, thumbnail_path, "webp", thumbnail_out_path, (256, 256))
                futures.append((future_img, future_thumb, image))

            for future_img, future_thumb, image in futures:
                img_path = future_img.result()
                thumbnail_path = future_thumb.result()

                img_path = "/".join(img_path.split("/")[1:])
                thumbnail_path = "/".join(thumbnail_path.split("/")[1:])
                img_title = image.split("_")[1].split(".")[0] if image.split("_")[1] else ""
                output.append(f'<a href="{img_path}" data-lightbox="{html_class}" data-title="{img_title}" data-alt="{img_title}"><img src="{thumbnail_path}" loading="lazy"></a>\n')
        return "".join(output) + "</div>\n"


    def shrink_and_compress_image(self, src_image_path: str, image_format: str, output_path: str, image_dimensions: tuple[int, int] = (0, 0)) -> str:
        try:
            output_name = f'{hashlib.sha256(src_image_path.split("/")[-1].encode("utf-8")).hexdigest()}.{image_format}'
            if output_name in os.listdir(output_path): return output_path + output_name
            output_path += output_name
            with Image.open(src_image_path) as im:
                if image_dimensions != (0, 0) and (im.size[0] > image_dimensions[0] or im.size[1] > image_dimensions[1]): im.thumbnail(image_dimensions)
                im.save(output_path, image_format)
            return output_path
        except Exception as e:
            print("cannot process", src_image_path)
            print("ERROR:", e)
            return ""

    def map(self):
        pass

    def chapter(self, html_class: str, key: str) -> str:
        output = ["<div>"]
        meta = get_conf(f"{self.base_path}{key}/meta.toml", ["title"])
        if meta["title"] != "": output.append(self.heading("_".join(key.split("/")[:3]), meta["title"], 3))
        else: output.append(f'<div id="{"_".join(key.split("/")[:3])}">\n<div>\n')
        if key in self.images: output.append(self.gallery(html_class, key))
        return "".join(output) + "</div></div></div><br>"

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
