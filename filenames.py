def generate_title(analysis, channel_count):
    return f"{channel_count} channels | Transform: {analysis['transform']}"

def generate_image_filename(prefix, analysis, id = None):
    id_txt = ""
    if (id != None):
        id_txt = f"_{id}"
    return f"{prefix}_{analysis['transform']}{id_txt}.png"