import sys
import os
import Main

path = os.getcwd()+"/tests"
files = os.listdir(path)
new_file_name = "input"
index = 1
while new_file_name+str(index) + ".txt" in files:
    index += 1
new_file_name = new_file_name + str(index) + ".txt"

sys.stdout = open(path+"/"+new_file_name, 'w')

# do the magic
Main.main()

sys.stdout.close()