import datetime


class OutputUtil:

    @staticmethod
    def output(output):
        f = open("../output.txt", "a")
        f.write("\n" + output + " " + str(datetime.datetime.now()))
        f.close()
