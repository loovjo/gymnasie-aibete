def parameterToString(par):
    strFrom = par(0)
    strTo = par(1)
    if strFrom == strTo:
        return strFrom
    else:
        return strFrom + "->" + strTo

class ParameterSet:
    def __init__(self,randomActionMethod=TRandom(0.2,1/6),learningRate=0.03,futureDiscount=0.8):
        self.learningRate = learningRate
        self.futureDiscount = futureDiscount
        self.randomActionMethod = randomActionMethod

        self.results = []
    
    def loadFromDict(data):
        res = ParameterSet(**data["parameters"])
        res.results = data["results"]
        return res
    
    def addResult(self,loss,reward):
        self.results.append({
            "loss":loss,
            "reward":reward
        })

    def getPlotTitle(self):
        return ("LR=" + parameterToString(self.learningRate) + 
        "FD=" + parameterToString(self.futureDiscount) + 
        "RAM=" + parameterToString(self.randomActionMethod))

    def plot(self, pltCtx,plotAllResults=True):
        pltCtx.addData()

    def dictify(self):
        return {
            "learningRate": parameterToString(self.learningRate),
            "futureDiscount": parameterToString(self.futureDiscount),
            "randomActionMethod": parameterToString(self.randomActionMethod),
            "results": self.results
        }