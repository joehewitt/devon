#ifndef DEVON_LOGCATEGORY_H
#define DEVON_LOGCATEGORY_H

namespace Devon {

// ************************************************************************************************

class LogCategory
{
public:
    LogCategory(const std::string& name, bool disabled=false)
        :   mName(name),
            mDisabled(disabled)
    {
    }

    const std::string& GetName() const { return mName; }

    bool GetDisabled() const { return mDisabled; }
    void SetDisabled(bool disabled) { mDisabled = disabled; }

protected:
    std::string mName;
    bool mDisabled;
};

// ************************************************************************************************

extern LogCategory LogCategoryDefault;
extern LogCategory LogCategoryAssertion;
extern LogCategory LogCategoryException;
extern LogCategory LogCategoryLifetime;

// ************************************************************************************************

} // namespace Devon

#endif // DEVON_LOGCATEGORY_H
