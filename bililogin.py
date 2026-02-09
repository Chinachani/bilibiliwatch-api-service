import requests
import json
import time
import qrcode
from PIL import Image
import base64
from io import BytesIO
import os
import threading
import sys


class BilibiliLogin:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Referer': 'https://passport.bilibili.com/login',
            'Origin': 'https://passport.bilibili.com'
        })
        
    def get_qr_code(self):
        """
        获取登录二维码
        返回: dict 包含 qrcode_key 和 url
        """
        try:
            # 获取二维码登录信息
            url = 'https://passport.bilibili.com/x/passport-login/web/qrcode/generate'
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # 检查响应内容
            response_text = response.text
            if not response_text.strip():
                return {
                    'success': False,
                    'message': '服务器返回空响应'
                }
            
            try:
                data = response.json()
            except ValueError as json_error:
                return {
                    'success': False,
                    'message': f"JSON解析失败: {str(json_error)}"
                }
            
            if data['code'] == 0:
                qr_data = data['data']
                return {
                    'success': True,
                    'qrcode_key': qr_data['qrcode_key'],
                    'url': qr_data['url']
                }
            else:
                return {
                    'success': False,
                    'message': f"获取二维码失败: {data.get('message', '未知错误')}"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f"网络请求失败: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"请求失败: {str(e)}"
            }
    
    def generate_qr_image(self, url, save_path=None):
        """
        生成二维码图片
        
        Args:
            url: 二维码内容URL
            save_path: 保存路径，如果为None则不保存到文件
            
        Returns:
            dict: 包含成功状态和base64编码的图片数据
        """
        try:
            # 创建二维码
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)
            
            # 创建图片
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 转换为base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # 如果指定了保存路径，则保存到文件
            if save_path:
                img.save(save_path)
                
            return {
                'success': True,
                'base64': img_base64,
                'save_path': save_path,
                'pil_image': img  # 添加PIL图片对象
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"生成二维码失败: {str(e)}"
            }

    def show_qr_window(self, qr_image, qr_url, qrcode_key):
        """
        在窗口中显示二维码并处理登录状态
        
        Args:
            qr_image: PIL图片对象
            qr_url: 二维码URL
            qrcode_key: 二维码密钥
            
        Returns:
            dict: 登录结果
        """
        # 延迟导入，避免在无 GUI 环境（如容器）导入失败
        import tkinter as tk
        from tkinter import ttk
        from PIL import ImageTk
        self.login_result = None
        self.window_closed = False
        
        def create_window():
            # 创建主窗口
            root = tk.Tk()
            root.title("哔哩哔哩扫码登录")
            root.geometry("400x500")
            root.resizable(False, False)
            
            # 设置窗口居中
            root.update_idletasks()
            x = (root.winfo_screenwidth() // 2) - (400 // 2)
            y = (root.winfo_screenheight() // 2) - (500 // 2)
            root.geometry(f"400x500+{x}+{y}")
            
            # 标题
            title_label = tk.Label(root, text="🎬 哔哩哔哩扫码登录", font=("Arial", 16, "bold"))
            title_label.pack(pady=10)
            
            # 说明文字
            info_label = tk.Label(root, text="请使用哔哩哔哩APP扫描下方二维码", font=("Arial", 10))
            info_label.pack(pady=5)
            
            # 二维码图片
            # 调整图片大小
            qr_resized = qr_image.resize((250, 250), Image.Resampling.LANCZOS)
            qr_photo = ImageTk.PhotoImage(qr_resized)
            
            qr_label = tk.Label(root, image=qr_photo)
            qr_label.pack(pady=10)
            
            # 状态标签
            status_label = tk.Label(root, text="⏳ 等待扫码...", font=("Arial", 10), fg="blue")
            status_label.pack(pady=5)
            
            # 进度条
            progress = ttk.Progressbar(root, mode='indeterminate')
            progress.pack(pady=10, padx=50, fill='x')
            progress.start()
            
            # 手动输入URL按钮
            def copy_url():
                root.clipboard_clear()
                root.clipboard_append(qr_url)
                url_button.config(text="✅ 已复制到剪贴板")
                root.after(2000, lambda: url_button.config(text="📋 复制登录链接"))
            
            url_button = tk.Button(root, text="📋 复制登录链接", command=copy_url)
            url_button.pack(pady=5)
            
            # 关闭按钮
            def close_window():
                self.window_closed = True
                root.destroy()
            
            close_button = tk.Button(root, text="❌ 取消登录", command=close_window, bg="#ff4444", fg="white")
            close_button.pack(pady=10)
            
            # 检查登录状态的函数
            def check_login_status():
                if self.window_closed:
                    return
                    
                try:
                    result = self.check_qr_status(qrcode_key)
                    
                    if result['success']:
                        if result['status'] == 'success':
                            status_label.config(text="✅ 登录成功！", fg="green")
                            progress.stop()
                            progress.config(mode='determinate', value=100)
                            
                            # 获取用户信息
                            user_info = self.get_user_info(result['cookies'])
                            if user_info['success']:
                                status_label.config(text=f"✅ 欢迎，{user_info['username']}！")
                            
                            self.login_result = {
                                'success': True,
                                'cookies': result['cookies'],
                                'user_info': user_info if user_info['success'] else None,
                                'message': '登录成功'
                            }
                            
                            # 2秒后关闭窗口
                            root.after(2000, close_window)
                            return
                            
                        elif result['status'] == 'scanned':
                            status_label.config(text="📱 已扫码，请在手机上确认登录", fg="orange")
                            
                        elif result['status'] == 'expired':
                            status_label.config(text="⏰ 二维码已过期，请重新获取", fg="red")
                            progress.stop()
                            self.login_result = {
                                'success': False,
                                'message': '二维码已过期'
                            }
                            # 3秒后关闭窗口
                            root.after(3000, close_window)
                            return
                            
                        elif result['status'] == 'waiting':
                            status_label.config(text="⏳ 等待扫码...", fg="blue")
                    
                    # 继续检查
                    if not self.window_closed:
                        root.after(3000, check_login_status)
                        
                except Exception as e:
                    status_label.config(text=f"❌ 检查状态失败: {str(e)}", fg="red")
                    if not self.window_closed:
                        root.after(5000, check_login_status)
            
            # 开始检查登录状态
            root.after(1000, check_login_status)
            
            # 窗口关闭事件
            root.protocol("WM_DELETE_WINDOW", close_window)
            
            # 运行窗口
            root.mainloop()
        
        # 在新线程中创建窗口
        window_thread = threading.Thread(target=create_window)
        window_thread.daemon = True
        window_thread.start()
        window_thread.join()
        
        # 返回登录结果
        if self.login_result:
            return self.login_result
        else:
            return {
                'success': False,
                'message': '用户取消登录或窗口被关闭'
            }
    
    def check_qr_status(self, qrcode_key):
        """
        检查二维码扫描状态
        
        Args:
            qrcode_key: 二维码密钥
            
        Returns:
            dict: 包含状态信息
        """
        try:
            params = {'qrcode_key': qrcode_key}
            response = self.session.get(
                'https://passport.bilibili.com/x/passport-login/web/qrcode/poll',
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data['code'] == 0:
                status_data = data['data']
                code = status_data['code']
                
                status_map = {
                    86101: {'status': 'waiting', 'message': '未扫码'},
                    86090: {'status': 'scanned', 'message': '已扫码，等待确认'},
                    86038: {'status': 'expired', 'message': '二维码已过期'},
                    0: {'status': 'success', 'message': '登录成功'}
                }
                
                result = status_map.get(code, {'status': 'unknown', 'message': f'未知状态码: {code}'})
                result['success'] = True
                result['code'] = code
                
                # 如果登录成功，提取cookies和用户信息
                if code == 0:
                    result['url'] = status_data.get('url', '')
                    result['cookies'] = self._extract_cookies_from_response(response)
                    
                return result
            else:
                return {
                    'success': False,
                    'message': f"检查状态失败: {data.get('message', '未知错误')}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"请求失败: {str(e)}"
            }
    
    def _extract_cookies_from_response(self, response):
        """
        从响应中提取cookies
        
        Args:
            response: requests响应对象
            
        Returns:
            dict: cookies字典
        """
        cookies = {}
        for cookie in self.session.cookies:
            cookies[cookie.name] = cookie.value
        return cookies
    
    def save_cookies_to_file(self, cookies, file_path='cookies.txt'):
        """
        保存cookies到文件
        
        Args:
            cookies: cookies字典
            file_path: 文件路径
            
        Returns:
            dict: 保存结果
        """
        try:
            # 转换为字符串格式
            cookie_str = '; '.join([f'{k}={v}' for k, v in cookies.items()])
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cookie_str)
                
            return {
                'success': True,
                'message': f'Cookies已保存到 {file_path}',
                'file_path': file_path
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'保存cookies失败: {str(e)}'
            }
    
    def get_user_info(self, cookies=None):
        """
        获取用户信息
        
        Args:
            cookies: cookies字典，如果为None则使用session中的cookies
            
        Returns:
            dict: 用户信息
        """
        try:
            if cookies:
                # 更新session的cookies
                for name, value in cookies.items():
                    self.session.cookies.set(name, value)
            
            response = self.session.get('https://api.bilibili.com/x/web-interface/nav')
            response.raise_for_status()
            
            data = response.json()
            
            if data['code'] == 0:
                user_data = data['data']
                return {
                    'success': True,
                    'uid': user_data.get('mid'),
                    'username': user_data.get('uname'),
                    'face': user_data.get('face'),
                    'level': user_data.get('level_info', {}).get('current_level'),
                    'vip_status': user_data.get('vipStatus'),
                    'is_login': user_data.get('isLogin', False)
                }
            else:
                return {
                    'success': False,
                    'message': f"获取用户信息失败: {data.get('message', '未知错误')}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"请求失败: {str(e)}"
            }
    
    def login_with_qr_code(self, save_cookies=True, cookie_file='cookies.txt', show_qr=True, qr_save_path='qrcode.png'):
        """
        完整的二维码登录流程（保存二维码到文件）
        
        Args:
            save_cookies: 是否保存cookies到文件
            cookie_file: cookies文件路径
            show_qr: 是否显示二维码信息
            qr_save_path: 二维码图片保存路径
            
        Returns:
            dict: 登录结果
        """
        print("🚀 开始哔哩哔哩扫码登录...")
        
        # 1. 获取二维码
        print("📱 正在获取登录二维码...")
        qr_result = self.get_qr_code()
        
        if not qr_result['success']:
            return qr_result
        
        qrcode_key = qr_result['qrcode_key']
        qr_url = qr_result['url']
        
        print(f"✅ 二维码获取成功")
        
        # 2. 生成二维码图片并打印 URL
        if show_qr:
            print("🖼️ 正在生成二维码图片...")
            img_result = self.generate_qr_image(qr_url, qr_save_path)

            if img_result['success']:
                print(f"✅ 二维码已保存到: {qr_save_path}")
            else:
                print(f"⚠️ 二维码图片生成失败: {img_result['message']}")

            print(f"📱 请使用哔哩哔哩APP扫描二维码登录")
            print(f"🔗 登录URL: {qr_url}")
        
        # 3. 轮询检查登录状态
        print("⏳ 等待扫码登录...")
        max_attempts = 60  # 最多等待5分钟
        attempt = 0
        
        while attempt < max_attempts:
            status_result = self.check_qr_status(qrcode_key)
            
            if not status_result['success']:
                return status_result
            
            status = status_result['status']
            message = status_result['message']
            
            if status == 'waiting':
                print(f"⏳ {message}... ({attempt + 1}/{max_attempts})")
            elif status == 'scanned':
                print(f"📱 {message}")
            elif status == 'expired':
                return {
                    'success': False,
                    'message': '二维码已过期，请重新获取'
                }
            elif status == 'success':
                print(f"🎉 {message}")
                
                # 4. 保存cookies
                cookies = status_result['cookies']
                if save_cookies and cookies:
                    save_result = self.save_cookies_to_file(cookies, cookie_file)
                    if save_result['success']:
                        print(f"💾 {save_result['message']}")
                    else:
                        print(f"⚠️ {save_result['message']}")
                
                # 5. 获取用户信息
                print("👤 正在获取用户信息...")
                user_info = self.get_user_info(cookies)
                
                if user_info['success']:
                    print(f"✅ 登录成功！")
                    print(f"👤 用户名: {user_info['username']}")
                    print(f"UID: {user_info['uid']}")
                    print(f"⭐ 等级: LV{user_info['level']}")
                    
                    return {
                        'success': True,
                        'message': '登录成功',
                        'cookies': cookies,
                        'user_info': user_info
                    }
                else:
                    print(f"⚠️ 获取用户信息失败: {user_info['message']}")
                    return {
                        'success': True,
                        'message': '登录成功但获取用户信息失败',
                        'cookies': cookies,
                        'user_info': None
                    }
            
            time.sleep(5)  # 每5秒检查一次
            attempt += 1
        
        return {
            'success': False,
            'message': '登录超时，请重试'
        }
    
    def login_with_qr_window(self, save_cookies=True, cookie_file='cookies.txt'):
        """
        在窗口中显示二维码的登录流程
        
        Args:
            save_cookies: 是否保存cookies到文件
            cookie_file: cookies文件路径
            
        Returns:
            dict: 登录结果
        """
        print("🚀 开始哔哩哔哩扫码登录（窗口模式）...")
        
        # 1. 获取二维码
        print("📱 正在获取登录二维码...")
        qr_result = self.get_qr_code()
        
        if not qr_result['success']:
            print(f"❌ 获取二维码失败: {qr_result['message']}")
            return qr_result
            
        print("✅ 二维码获取成功")
        qrcode_key = qr_result['qrcode_key']
        qr_url = qr_result['url']
        
        # 2. 生成二维码图片
        print("🖼️ 正在生成二维码图片...")
        img_result = self.generate_qr_image(qr_url)
        
        if not img_result['success']:
            print(f"❌ 生成二维码图片失败: {img_result['message']}")
            return img_result
            
        print("✅ 二维码生成成功，正在打开登录窗口...")
        
        # 3. 显示窗口并等待登录
        login_result = self.show_qr_window(img_result['pil_image'], qr_url, qrcode_key)
        
        if login_result['success']:
            print("🎉 登录成功！")
            cookies = login_result['cookies']
            user_info = login_result['user_info']
            
            if user_info:
                print(f"✅ 欢迎，{user_info['username']}！")
                print(f"🆔 UID: {user_info['uid']}")
                print(f"⭐ 等级: {user_info['level']}")
            
            # 4. 保存cookies
            if save_cookies:
                print(f"💾 正在保存cookies到: {cookie_file}")
                save_result = self.save_cookies_to_file(cookies, cookie_file)
                
                if save_result['success']:
                    print("✅ Cookies保存成功")
                else:
                    print(f"❌ Cookies保存失败: {save_result['message']}")
            
            return login_result
        else:
            print(f"❌ 登录失败: {login_result['message']}")
            return login_result

def main():
    """
    主函数 - 演示扫码登录功能
    """
    print("=" * 50)
    print("🎬 哔哩哔哩扫码登录工具")
    print("=" * 50)
    print("请选择登录模式：")
    print("1. 窗口模式（推荐） - 在弹出窗口中显示二维码")
    print("2. 文件模式 - 保存二维码为图片文件")
    print("=" * 50)
    
    while True:
        try:
            choice = input("请输入选择 (1/2): ").strip()
            if choice in ['1', '2']:
                break
            else:
                print("❌ 无效选择，请输入 1 或 2")
        except KeyboardInterrupt:
            print("\n❌ 用户取消操作")
            return
    
    login = BilibiliLogin()
    
    try:
        if choice == '1':
            # 窗口模式
            result = login.login_with_qr_window(
                save_cookies=True,
                cookie_file='cookies.txt'
            )
        elif choice == '2':
            # 文件模式
            result = login.login_with_qr_code(
                save_cookies=True,
                cookie_file='cookies.txt',
                show_qr=True,
                qr_save_path='qrcode.png'
            )
        
        if result['success']:
            print("\n" + "=" * 50)
            print("🎉 登录完成！")
            print("=" * 50)
        else:
            print("\n" + "=" * 50)
            print(f"❌ 登录失败: {result['message']}")
            print("=" * 50)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户取消登录")
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")

if __name__ == '__main__':
    main()
