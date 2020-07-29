def createGenerator() :
    mylist = ['a','b','c']
    for i in range(len(mylist)) :
        empty= mylist[i]
        yield empty
mygenerator = createGenerator() # create a generator
for i in range(3):
    print(next(mygenerator)) # mygenerator is an object!