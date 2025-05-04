
const string gc_str = "GlobalConstStr";
string return_global_const_string()
{
    return gc_str;
}

string g_str = "GlobalStr";
string return_global_string()
{
    return g_str;
}

string init_global()
{
    return "GlobalInitStr";
}
string g_istr = init_global();
string return_global_init_string()
{
    return g_istr;
}

void test_PrintString()
{
    PrintString("LocalStr");
}

int return_int()
{
    return 42;
}

int test_mock()
{
    return GetHitDice(OBJECT_SELF);
}

object return_object_invalid()
{
    return OBJECT_INVALID;
}

object return_object_self()
{
    return OBJECT_SELF;
}

void call_GetIsReactionTypeFriendly()
{
    GetIsReactionTypeFriendly(OBJECT_INVALID, OBJECT_SELF);
}

object return_module()
{
    return GetModule();
}

struct Testing1 {
    string m_str;
    float m_flt;
    int m_int;
};

struct Testing1 take_and_return_struct1(struct Testing1 in)
{
    PrintInteger(in.m_int == 42);
    PrintInteger(in.m_flt >= 3.13 && in.m_flt <= 3.15);
    PrintInteger(in.m_str == "hello");
    in.m_str = in.m_str + in.m_str;
    PrintInteger(in.m_str == "hellohello");
    in.m_flt *= 2;
    PrintInteger(in.m_flt >= 6.26 && in.m_flt <= 6.30);
    in.m_int *= 4;
    PrintInteger(in.m_int == 168);
    return in;
}

struct Testing2 {
    struct Testing1 m_t1;
    object m_obj;
};

struct Testing2 take_and_return_struct2(struct Testing2 in)
{
    struct Testing2 copy;
    copy.m_t1 = take_and_return_struct1(in.m_t1);
    PrintInteger(in.m_obj == OBJECT_SELF);
    copy.m_obj = OBJECT_SELF;
    return copy;
}

effect return_effect()
{
    return EffectSlow();
}

void take_effect(effect eSomething)
{
    PrintInteger(GetEffectType(eSomething) == EFFECT_TYPE_SLOW);
}

vector take_and_modify_vector(vector v)
{
    v.x += 1.0;
    return v;
}

void main()
{
    test_PrintString();
}
