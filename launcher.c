/* 双击启动器:找到同目录下的 sessions_gui.pyw,用 pythonw.exe 打开。
 * 用 -mwindows 编译,不会弹出黑色 cmd 窗口。 */
#include <windows.h>
#include <stdio.h>

int WINAPI WinMain(HINSTANCE hInst, HINSTANCE hPrev, LPSTR cmd, int show)
{
    char exe[MAX_PATH];
    char script[MAX_PATH + 2];
    char cmdline[MAX_PATH * 2 + 16];

    if (!GetModuleFileNameA(NULL, exe, MAX_PATH)) return 1;
    char *slash = strrchr(exe, '\\');
    if (slash) *slash = '\0';

    snprintf(script, sizeof script, "%s\\sessions_gui.pyw", exe);
    if (GetFileAttributesA(script) == INVALID_FILE_ATTRIBUTES) {
        MessageBoxA(NULL,
            "找不到 sessions_gui.pyw。\n请把这个 exe 和 pyw 放在同一个文件夹里。",
            "Claude 对话管理", MB_ICONERROR);
        return 2;
    }

    snprintf(cmdline, sizeof cmdline, "\"pythonw.exe\" \"%s\"", script);

    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof si);
    si.cb = sizeof si;
    ZeroMemory(&pi, sizeof pi);

    if (!CreateProcessA(NULL, cmdline, NULL, NULL, FALSE,
                        CREATE_NO_WINDOW, NULL, exe, &si, &pi)) {
        MessageBoxA(NULL,
            "启动失败:找不到 pythonw.exe。\n请确认 Python 已正确安装并加入 PATH。",
            "Claude 对话管理", MB_ICONERROR);
        return 3;
    }
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    return 0;
}
