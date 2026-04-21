class AIHubService:
    def __init__(self):
        pass

    async def gentxt(self, request):
        return {"content": "test response"}

    async def gentxt_stream(self, request):
        yield "test"

    async def genimg(self, request):
        return {"images": ["test"]}