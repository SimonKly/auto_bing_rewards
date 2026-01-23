import uvicorn
import argparse
import os
from app.main import app


def main():
    parser = argparse.ArgumentParser(description="Bing Rewards Automation")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode (shows browser window and slows down actions)")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers")
    
    args = parser.parse_args()
    
    # 设置环境变量，控制是否使用无头模式和调试模式
    os.environ["HEADLESS_MODE"] = "1" if not args.debug else "0"
    os.environ["DEBUG_MODE"] = "1" if args.debug else "0"
    
    print(f"Starting Bing Rewards Automation Server at http://{args.host}:{args.port}")
    print(f"Debug mode: {'ON' if args.debug else 'OFF'}")
    print(f"Headless mode: {'ON' if args.headless else 'OFF'}")
    print("Press Ctrl+C to stop")
    
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=False,  # 生产环境中设置为False
        workers=args.workers
    )


if __name__ == "__main__":
    main()