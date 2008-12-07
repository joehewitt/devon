// Devon
#include <Devon/TestRunner.h>
#include <Devon/logging.h>

// STL
#include <exception>

// stdlib
#include <signal.h>

#ifdef WIN32
#include <direct.h>
#endif

//**************************************************************************************************

// Implement this function in your main test file to return your test environment
Devon::TestEnvironment* GetTestEnvironment();

//**************************************************************************************************

void HandleBreak(int sig_num)
{
}

void HandleCrash(int sig_num)
{
    //WARN("Program segfaulted. Go debug it, cowboy.");
    //while (1) 1;
}

void HandleTerminate()
{
    //WARN("Program segfaulted. Go debug it, cowboy.");
    //while (1) 1;
}

#ifdef WIN32a
__stdcall
WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow)
#else
int
main(int argc, char* argv[])
#endif
{
    // Prevent the program from crashing so the debugger can grab it
    signal(SIGINT, HandleBreak);
    
    #ifdef DARWIN
    signal(SIGSEGV, HandleCrash);
    std::set_terminate(HandleTerminate);
    #endif
    
    std::string mode, target;
    
    for (unsigned int i = 0; i < argc; ++i)
    {
        if (i == 0)
        {
            // Properly set the working directory as the path that the exe is located in
            std::string path = argv[0];
            unsigned int lastSlash = path.rfind('/');
            if (lastSlash != -1)
            {
                const std::string wd = path.substr(0, lastSlash);
                chdir(wd.c_str());
            }
        }
        else if (i+1 < argc)
        {
            const char* arg = argv[i];
            if (*arg == '-' && *(arg+1) == '-')
            {
                arg += 2;
                if (!strcmp(arg, "mode"))
                    mode = argv[++i];
                else if (!strcmp(arg, "target"))
                    target = argv[++i];
            }
        }
    }
    
    
    Devon::TestEnvironment* env = GetTestEnvironment();
    Devon::Run(env, mode, target);

    LOG_EXIT();

    return 0;
}

//**************************************************************************************************
