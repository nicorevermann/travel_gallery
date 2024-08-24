#!/usr/bin/env python3

import os
import tomllib

def setup(conf_file, keys):
    with open(conf_file, "rb") as fh: conf = tomllib.load(fh)
    return [conf[k] if k in conf else "" for k in keys]


def generate_content(base_url, filetree, template, output_path):

    for year in sorted(filetree, reverse=True):
        for destination in sorted(filetree[year]):
            content = ""
            path = base_url + year + "/" + destination + "/"
            with open(path + "meta.toml", "rb") as fh: meta = tomllib.load(fh)
            title = meta["title"]
            content += f'<div id="{year}_{destination}">\n<h2>{title}</h2>\n<div>\n'

            for chapter in sorted(filetree[year][destination]):
                path = base_url + year + "/" + destination + "/"
                if "files" not in chapter:
                    path += chapter + "/"
                    if not os.path.isfile(path + "meta.toml"): open(path + "meta.toml", "a").close()
                    with open(path + "meta.toml", "rb") as fh: meta = tomllib.load(fh)
                    title = meta["title"] if "title" in meta else ""
                    
                    content += f'<div class="chapter">\n<h4>{title}</h4>\n<div class="images">\n' if title != "" else f'<div class="chapter">\n<div class="images">\n'

                    for file in sorted(filetree[year][destination][chapter]["files"]):
                        if file.endswith(("jpg", "jpeg", "png")):
                            img_path = path + file
                            img_title = file.split(".")[0].split("_")[1]
                            content += f'<a href="{img_path}" data-lightbox="{year}_{destination}" data-title="{img_title}" data-alt="{img_title}"><img src="{img_path}" loading="lazy"></a>\n'
                    content += '</div>\n</div>\n<br><center>---<center><br>\n\n'
                    continue

                content += '<div class="images">'
                for file in sorted(filetree[year][destination][chapter]):
                    if file.endswith(("jpg", "jpeg", "png")):
                        img_path = path + file
                        img_title = file.split(".")[0].split("_")[1]
                        content += f'<a href="{img_path}" data-lightbox="{year}_{destination}" data-title="{img_title}" data-alt="{img_title}"><img src="{img_path}" loading="lazy"></a>\n'
                content += "</div>"

            content += '</div>\n</div>\n<br><hr>\n\n'

            with open(template, "r") as fh: page = fh.read()
            with open(output_path + f"{year}_{destination}.html", "w") as fh: fh.write(page.replace("{content}", content))
            

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
    parameters = setup("conf/conf.toml", ["img_path", "template_links", "template_trip", "output_path"])

    img_path = parameters.pop(0)
    template_links = parameters.pop(0)
    template_trip = parameters.pop(0)
    output_path = parameters.pop(0)

    filetree = generate_filetree(img_path)

    generate_links(img_path, filetree, template_links, output_path)
    generate_content(img_path, filetree, template_trip, output_path)
