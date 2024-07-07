import os
import zipfile
from pathlib import Path, PurePath

import typer
from bs4 import BeautifulSoup, element

IMAGE_SUFFIX = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".avif"]


def main(
    epub: Path = typer.Argument(..., help="epub file"),
    output: Path = typer.Option(None, "--output", "-o", help="Path to output folder"),
):
    """
    Convert epub to cbz

    Args:
        epubs (list[Path]): epub files
        output (Path): output directory
    """
    if output is None:
        output = Path.cwd() / f"{epub.stem}"
    output.mkdir(parents=True, exist_ok=True)
    epub2cbz(epub, output)


def epub2cbz(epub: Path, output: Path):
    """
    Convert epub to cbz

    Args:
        epub (Path): epub file
        output (Path): output directory
    """
    with zipfile.ZipFile(epub, "r") as z:
        container_xml = z.read("META-INF/container.xml").decode()
        opf_path = container_xml.split('full-path="')[1].split('"')[0]
        opf = z.read(opf_path).decode()
        soup = BeautifulSoup(opf, "xml")
        items: dict[str, str] = {item.get("id"): item.get("href") for item in soup.find_all("item")}
        itemrefs = [i.get("idref") for i in soup.find_all("itemref")]

        images: list[PurePath] = []
        for itemref in itemrefs:
            item_path = PurePath(opf_path).parent / items[itemref]

            # when item is image
            if item_path.suffix in IMAGE_SUFFIX:
                images.append(item_path)

            # when item is xhtml
            elif item_path.suffix in (".xhtml", ".html"):
                xhtml = z.read(item_path.as_posix()).decode()
                soup = BeautifulSoup(xhtml, "html.parser")
                image_tag = soup.find("image") or soup.find("img")
                if type(image_tag) == element.Tag:
                    link = image_tag.get("xlink:href") or image_tag.get("src")
                    if type(link) is list:
                        images.extend([item_path.parent / link_item for link_item in link])
                    elif type(link) is str:
                        images.append(item_path.parent / link)

        for index, image_path in enumerate(images, 1):
            image = z.read(PurePath(os.path.normpath(image_path)).as_posix())
            image_path = output / f"{index:05}{image_path.suffix}"
            with open(image_path, "wb") as f:
                f.write(image)


if __name__ == "__main__":
    typer.run(main)
