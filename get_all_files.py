import os


def get_all(path, ext=""):
    files = []
    # name= []
    if ext != "":

        for r, D, f in os.walk(path):
            for file in f:
                if ext in file:
                    # name.append(file)
                    files.append(os.path.normpath(os.path.join(r, file)).replace("\\", "/"))

    else:

        for r, D, f in os.walk(path):
            for file in f:
                # name.append(file)
                files.append(os.path.normpath(os.path.join(r, file)).replace("\\", "/"))

    files.sort(key=os.path.getmtime)
    # files=natsorted(files)
    # name = natsorted(name)

    return files


if __name__ == "__main__":
    path = r'C:/Users/Python/Desktop/Data'
    d = get_all(path)
