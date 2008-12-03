//   Contains code by Inv Softworks LLC, www.flexhex.com

// Windows
#define _WIN32_WINNT		0x0500		// Windows 2000 or later

#include <windows.h>
#include <shlobj.h>
#include <iostream>
#include <string>

const unsigned int REPARSE_MOUNTPOINT_HEADER_SIZE = 8;

using namespace std;

namespace Link {

// *************************************************************************************************
// Local Helpers

struct REPARSE_MOUNTPOINT_DATA_BUFFER
{
    DWORD ReparseTag;
    DWORD ReparseDataLength;
    WORD Reserved;
    WORD ReparseTargetLength;
    WORD ReparseTargetMaximumLength;
    WORD Reserved1;
    WCHAR ReparseTarget[1];
};

static void
PrintError(DWORD dwErr)
{
    char szMsg[256];
    DWORD dwFlags = FORMAT_MESSAGE_IGNORE_INSERTS |
                    FORMAT_MESSAGE_MAX_WIDTH_MASK |
                    FORMAT_MESSAGE_FROM_SYSTEM;

    if (!::FormatMessage(dwFlags, NULL, dwErr, 0, szMsg, sizeof(szMsg), NULL))
        ::strcpy(szMsg, "Unknown error.");
    cout << szMsg << endl;
}

static HANDLE
OpenDirectory(const char* path, bool bReadWrite)
{
    // Obtain backup/restore privilege in case we don't have it
    HANDLE hToken;
    TOKEN_PRIVILEGES tp;
    ::OpenProcessToken(::GetCurrentProcess(), TOKEN_ADJUST_PRIVILEGES, &hToken);
    ::LookupPrivilegeValue(NULL,
                            (bReadWrite ? SE_RESTORE_NAME : SE_BACKUP_NAME),
                            &tp.Privileges[0].Luid);
    tp.PrivilegeCount = 1;
    tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED;
    ::AdjustTokenPrivileges(hToken, FALSE, &tp, sizeof(TOKEN_PRIVILEGES), NULL, NULL);
    ::CloseHandle(hToken);

    // Open the directory
    DWORD dwAccess = bReadWrite ? (GENERIC_READ | GENERIC_WRITE) : GENERIC_READ;
    HANDLE hDir = ::CreateFile(path, dwAccess, 0, NULL, OPEN_EXISTING,
                        FILE_FLAG_OPEN_REPARSE_POINT | FILE_FLAG_BACKUP_SEMANTICS, NULL);

  return hDir;
}

#define DIR_ATTR  (FILE_ATTRIBUTE_DIRECTORY | FILE_ATTRIBUTE_REPARSE_POINT)

/**
 * Returns true if the specified path is a directory link.
 */

static bool
IsDirectoryLink(const char* dir)
{
    DWORD dwAttr = ::GetFileAttributes(dir);
    if (dwAttr == -1) return FALSE;  // Not exists
    if ((dwAttr & DIR_ATTR) != DIR_ATTR) return FALSE;  // Not dir or no reparse point

    HANDLE hDir = OpenDirectory(dir, FALSE);
    if (hDir == INVALID_HANDLE_VALUE) return FALSE;  // Failed to open directory

    BYTE buf[MAXIMUM_REPARSE_DATA_BUFFER_SIZE];
    REPARSE_MOUNTPOINT_DATA_BUFFER& ReparseBuffer = (REPARSE_MOUNTPOINT_DATA_BUFFER&)buf;
    DWORD dwRet;
    BOOL br = ::DeviceIoControl(hDir, FSCTL_GET_REPARSE_POINT, NULL, 0, &ReparseBuffer,
                                        MAXIMUM_REPARSE_DATA_BUFFER_SIZE, &dwRet, NULL);
    ::CloseHandle(hDir);
    return br ? (ReparseBuffer.ReparseTag == IO_REPARSE_TAG_MOUNT_POINT) : FALSE;
}

/**
 * Returns the concrete target path of a directory link.
 */

static std::string
GetDirectoryLinkTarget(const char* linkPath)
{
    char szPath[MAX_PATH] = { 0 };  // Buffer for returned path

    if (!IsDirectoryLink(linkPath))
        return "";

    // Open for reading only (see OpenDirectory definition above)
    HANDLE hDir = OpenDirectory(linkPath, false);

    BYTE buf[MAXIMUM_REPARSE_DATA_BUFFER_SIZE];  // We need a large buffer
    REPARSE_MOUNTPOINT_DATA_BUFFER& ReparseBuffer = (REPARSE_MOUNTPOINT_DATA_BUFFER&)buf;
    DWORD dwRet;

    if (::DeviceIoControl(hDir, FSCTL_GET_REPARSE_POINT, NULL, 0, &ReparseBuffer,
                                    MAXIMUM_REPARSE_DATA_BUFFER_SIZE, &dwRet, NULL))
    {
        // Success

        LPCWSTR pPath = ReparseBuffer.ReparseTarget;
        if (wcsncmp(pPath, L"\\??\\", 4) == 0)
            pPath += 4;  // Skip 'non-parsed' prefix
        ::WideCharToMultiByte(CP_ACP, 0, pPath, -1, szPath, MAX_PATH, NULL, NULL);
    }
    else
    {
        DWORD dr = ::GetLastError();
    }

    ::CloseHandle(hDir);
    return szPath;
}

static void
CreateDirectoryLink(const char* linkPath, const char* linkTarget)
{   
    if (!::CreateDirectory(linkPath, NULL))
        throw ::GetLastError();

    HANDLE hDir = OpenDirectory(linkPath, true);
    if (hDir == INVALID_HANDLE_VALUE)
        throw ::GetLastError();

    BYTE buf[sizeof(REPARSE_MOUNTPOINT_DATA_BUFFER) + MAX_PATH * sizeof(WCHAR)] = { 0 };
    REPARSE_MOUNTPOINT_DATA_BUFFER& ReparseBuffer = (REPARSE_MOUNTPOINT_DATA_BUFFER&)buf;

    char szTarget[MAX_PATH] = "\\??\\";
    ::strcat(szTarget, linkTarget);
    ::strcat(szTarget, "\\");

    ReparseBuffer.ReparseTag = IO_REPARSE_TAG_MOUNT_POINT;
    int len = ::MultiByteToWideChar(CP_ACP, 0, szTarget, -1, ReparseBuffer.ReparseTarget, MAX_PATH);
    ReparseBuffer.ReparseTargetMaximumLength = (len--) * sizeof(WCHAR);
    ReparseBuffer.ReparseTargetLength = len * sizeof(WCHAR);
    ReparseBuffer.ReparseDataLength = ReparseBuffer.ReparseTargetLength + 12;

    DWORD dwRet;
    if (!::DeviceIoControl(hDir, FSCTL_SET_REPARSE_POINT, &ReparseBuffer,
            ReparseBuffer.ReparseDataLength+REPARSE_MOUNTPOINT_HEADER_SIZE, NULL, 0, &dwRet, NULL))
    {
        dwRet = ::GetLastError();
        ::CloseHandle(hDir);
        ::RemoveDirectory(linkPath);
        throw dwRet;
    }

    ::CloseHandle(hDir);
}

// *************************************************************************************************

} // namespace Link

// *************************************************************************************************

int
main(int argc, char* argv[])
{
    int iRetCode = EXIT_SUCCESS;

    if (argc != 3)
    {
        cout << "Usage: ln file hardlink" << endl << endl;
        cout << "Example: ln c:\\Blake\\Photos c:\\Photos" << endl << endl;
        ::exit(EXIT_SUCCESS);
    }

    ::CoInitialize(NULL);

    try
    {
        char* pszName;

        char szPath[MAX_PATH], szLink[MAX_PATH];
        ::strcpy(szLink, argv[2]);
        unsigned int len = ::strlen(szLink);

        // Remove trailing backslash
        if (szLink[len-1] == '\\')
            szLink[--len] = '\0';  

        // Check if a link target is being queries
        if (::strlen(argv[1]) == 2 && !::strcmp(argv[1], "-q"))
            cout << Link::GetDirectoryLinkTarget(szLink);
        else
        {
            if (!::GetFullPathName(argv[1], MAX_PATH, szPath, &pszName))
                throw ::GetLastError();
            len = ::strlen(szPath);

            // Remove trailing backslash
            if (szPath[len-1] == '\\')
                szPath[--len] = '\0';  

            if (szPath[len-1] != ':')
            {
                DWORD dwAttr = ::GetFileAttributes(szPath);
                if (dwAttr == -1)
                    throw ::GetLastError();
                if ((dwAttr & FILE_ATTRIBUTE_DIRECTORY) == 0) // If file
                {   
                    if (!::CreateHardLink(argv[2], argv[1], NULL))
                        throw ::GetLastError();
                }
                else    // Directory
                    Link::CreateDirectoryLink(szLink, szPath);
            }
            else  // Root directory
                Link::CreateDirectoryLink(szLink, szPath);
        }
    }
    catch (DWORD dwErrCode)
    {
        Link::PrintError(dwErrCode);
        iRetCode = EXIT_FAILURE;
    }

    ::CoUninitialize();
    ::exit(iRetCode);
}
