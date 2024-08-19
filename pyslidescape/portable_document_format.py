import os
import img2pdf


def images_to_pdf(list_of_image_paths, out_path):
    tmp_path = out_path + ".part"
    with open(tmp_path, "wb") as f:
        f.write(img2pdf.convert(list_of_image_paths))
    os.rename(tmp_path, out_path)
