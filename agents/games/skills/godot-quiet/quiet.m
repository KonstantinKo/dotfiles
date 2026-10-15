// Injected into Godot via DYLD_INSERT_LIBRARIES. Keeps the macOS display server
// (and therefore the real GPU renderer) but never lets a window reach the screen.
#import <AppKit/AppKit.h>
#import <objc/runtime.h>

static IMP orig_set_policy;

static BOOL quiet_set_policy(id self, SEL _cmd, NSApplicationActivationPolicy policy) {
	return ((BOOL (*)(id, SEL, NSApplicationActivationPolicy))orig_set_policy)(self, _cmd, NSApplicationActivationPolicyProhibited);
}
static void quiet_noop(id self, SEL _cmd) {}
static void quiet_noop_arg(id self, SEL _cmd, id arg) {}
static void quiet_noop_bool(id self, SEL _cmd, BOOL flag) {}
static void quiet_noop_order(id self, SEL _cmd, NSWindowOrderingMode mode, NSInteger other) {}
static void quiet_noop_options(id self, SEL _cmd, NSUInteger options) {}
static BOOL quiet_no(id self, SEL _cmd) { return NO; }
static BOOL quiet_no_options(id self, SEL _cmd, NSUInteger options) { return NO; }
static NSInteger quiet_attention(id self, SEL _cmd, NSUInteger type) { return 0; }
static NSWindowOcclusionState quiet_occlusion(id self, SEL _cmd) { return NSWindowOcclusionStateVisible; }
static NSModalResponse quiet_modal(NSAlert *self, SEL _cmd) {
	fprintf(stderr, "godot-quiet: suppressed alert: %s %s\n", self.messageText.UTF8String, self.informativeText.UTF8String);
	return NSAlertFirstButtonReturn;
}

static void replace(Class cls, const char *name, IMP imp) {
	Method method = class_getInstanceMethod(cls, sel_registerName(name));
	if (method) {
		method_setImplementation(method, imp);
	}
}

__attribute__((constructor)) static void quiet_init(void) {
	Class app = [NSApplication class];
	orig_set_policy = method_getImplementation(class_getInstanceMethod(app, @selector(setActivationPolicy:)));
	replace(app, "setActivationPolicy:", (IMP)quiet_set_policy);
	replace(app, "activateIgnoringOtherApps:", (IMP)quiet_noop_bool);
	replace(app, "activate", (IMP)quiet_noop);
	replace(app, "requestUserAttention:", (IMP)quiet_attention);
	replace(app, "setPresentationOptions:", (IMP)quiet_noop_options);
	replace([NSRunningApplication class], "activateWithOptions:", (IMP)quiet_no_options);

	Class window = [NSWindow class];
	replace(window, "makeKeyAndOrderFront:", (IMP)quiet_noop_arg);
	replace(window, "orderFront:", (IMP)quiet_noop_arg);
	replace(window, "orderBack:", (IMP)quiet_noop_arg);
	replace(window, "orderFrontRegardless", (IMP)quiet_noop);
	replace(window, "orderWindow:relativeTo:", (IMP)quiet_noop_order);
	replace(window, "setIsVisible:", (IMP)quiet_noop_bool);
	replace(window, "makeKeyWindow", (IMP)quiet_noop);
	replace(window, "makeMainWindow", (IMP)quiet_noop);
	replace(window, "toggleFullScreen:", (IMP)quiet_noop_arg);
	replace(window, "miniaturize:", (IMP)quiet_noop_arg);
	replace(window, "occlusionState", (IMP)quiet_occlusion);

	replace([NSAlert class], "runModal", (IMP)quiet_modal);
}

// Mouse capture and cursor changes would otherwise hit the user's real pointer.
static CGError quiet_associate(boolean_t connected) { return kCGErrorSuccess; }
static CGError quiet_warp(CGPoint point) { return kCGErrorSuccess; }
static CGError quiet_cursor(CGDirectDisplayID display) { return kCGErrorSuccess; }

#define INTERPOSE(replacement, original) \
	__attribute__((used)) static struct { const void *r; const void *o; } interpose_##original \
			__attribute__((section("__DATA,__interpose"))) = { (const void *)&replacement, (const void *)&original }
INTERPOSE(quiet_associate, CGAssociateMouseAndMouseCursorPosition);
INTERPOSE(quiet_warp, CGWarpMouseCursorPosition);
INTERPOSE(quiet_cursor, CGDisplayHideCursor);
INTERPOSE(quiet_cursor, CGDisplayShowCursor);
