from pyz.worker import ZeebeWorker


class EchoIn:
    def __init__(self, input):
        self.input = input


class EchoOut:
    def __init__(self, output):
        self.output = output


def handler(input):
    print("handling")
    return {"output": f"Hello World, {input['input']}!"}


if __name__ == '__main__':
    worker = ZeebeWorker('localhost:26500')
    worker.register_task("echo", handler)
    worker.run()
